from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.cloud import storage
import joblib
import os

app = FastAPI()

GCS_BUCKET = os.environ.get("GCS_BUCKET", os.environ.get("CLOUD_BUCKET", ""))
GCS_MODEL_KEY = "models/latest/model.pkl"
MODEL_PATH = os.path.expanduser("~/models/model.pkl")



def download_model():
    """
    Tai file model.pkl tu Cloud Storage (Azure Blob / GCS) ve may khi server khoi dong.
    """
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

    azure_conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    azure_container = os.environ.get("AZURE_CONTAINER", os.environ.get("CLOUD_BUCKET"))

    if azure_conn_str and azure_container:
        try:
            from azure.storage.blob import BlobServiceClient
            blob_service_client = BlobServiceClient.from_connection_string(azure_conn_str)
            blob_client = blob_service_client.get_blob_client(container=azure_container, blob=GCS_MODEL_KEY)
            with open(MODEL_PATH, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())
            print(f"Model da duoc tai xuong tu Azure Container: {azure_container}/{GCS_MODEL_KEY}")
            return
        except Exception as e:
            print(f"Loi tai model tu Azure: {e}")

    gcs_bucket = os.environ.get("GCS_BUCKET", os.environ.get("CLOUD_BUCKET"))
    if gcs_bucket:
        try:
            from google.cloud import storage
            client = storage.Client()
            bucket = client.bucket(gcs_bucket)
            blob = bucket.blob(GCS_MODEL_KEY)
            blob.download_to_filename(MODEL_PATH)
            print(f"Model da duoc tai xuong tu GCS: gs://{gcs_bucket}/{GCS_MODEL_KEY}")
            return
        except Exception as e:
            print(f"Loi tai model tu GCS: {e}")

    print("Cloud credentials not set. Skipping model download.")


if os.environ.get("AZURE_STORAGE_CONNECTION_STRING") or os.environ.get("GCS_BUCKET") or os.environ.get("CLOUD_BUCKET"):
    download_model()


model = None
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
elif os.path.exists("models/model.pkl"):
    model = joblib.load("models/model.pkl")


class PredictRequest(BaseModel):
    features: list[float]


@app.get("/health")
def health():
    """
    Endpoint kiem tra suc khoe server.
    GitHub Actions goi endpoint nay sau khi deploy de xac nhan server dang chay.

    Tra ve: {"status": "ok"}
    """
    return {"status": "ok"}


@app.post("/predict")
def predict(req: PredictRequest):
    """
    Endpoint suy luan chinh.

    Dau vao : JSON {"features": [f1, f2, ..., f12]}
    Dau ra  : JSON {"prediction": <0|1|2>, "label": <"thap"|"trung_binh"|"cao">}

    Thu tu 12 dac trung (khop voi thu tu trong FEATURE_NAMES cua test):
        fixed_acidity, volatile_acidity, citric_acid, residual_sugar,
        chlorides, free_sulfur_dioxide, total_sulfur_dioxide, density,
        pH, sulphates, alcohol, wine_type
    """
    if len(req.features) != 12:
        raise HTTPException(status_code=400, detail="Expected 12 features (wine quality)")

    global model
    if model is None:
        if os.path.exists(MODEL_PATH):
            model = joblib.load(MODEL_PATH)
        elif os.path.exists("models/model.pkl"):
            model = joblib.load("models/model.pkl")
        else:
            raise HTTPException(status_code=500, detail="Model file not found")

    preds = model.predict([req.features])
    pred_val = int(preds[0])

    labels = {0: "thap", 1: "trung_binh", 2: "cao"}
    label_str = labels.get(pred_val, "unknown")

    return {"prediction": pred_val, "label": label_str}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
