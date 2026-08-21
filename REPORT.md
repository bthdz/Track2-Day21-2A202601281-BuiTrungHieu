# BÁO CÁO KẾT QUẢ LAB MLOPS THỰC HÀNH

**Họ và tên**: Bùi Trung Hiếu  
**Mã SV / Lớp**: 2A202601281 
**Khóa**: K3

---

## 1. Bộ Siêu Tham Số Đã Chọn Và Lý Do
- **Siêu tham số tối ưu lựa chọn**:
  - `n_estimators`: `300`
  - `max_depth`: `20`
  - `min_samples_split`: `2`
- **Lý do chọn**: Qua quá trình thử nghiệm 10 lần chạy trên MLflow UI với các bộ siêu tham số khác nhau (`n_estimators` từ 10 đến 500, `max_depth` từ 3 đến 30), cấu hình trên cho hiệu năng cao nhất trên tập đánh giá `eval.csv` với **Accuracy = 0.7560** và **F1-Score = 0.7552** vượt xa ngưỡng Eval Gate `0.70` của CI/CD pipeline.

---

## 2. So Sánh Hiệu Năng Giữa Các Tập Dữ Liệu
| Chỉ số | Lần 1 (2,998 mẫu - Bước 2) | Lần 2 (5,996 mẫu - Bước 3) | Nhận xét |
|---|:---:|:---:|---|
| **Accuracy** | 0.7560 | 0.7420 | Mô hình đạt 0.7420, vẫn vượt xa ngưỡng Eval Gate 0.70 và đủ điều kiện tự động triển khai lên VM. Việc chỉ số biến động nhẹ trên tập held-out là hoàn toàn bình thường khi nạp thêm dữ liệu mới. |
| **F1 Score** | 0.7552 | 0.7411 | Chỉ số F1 giữ mức ổn định cao (~0.7411), đảm bảo chất lượng mô hình cân bằng trên các phân lớp. |

---

## 3. Khó Khăn Gặp Phải Và Cách Giải Quyết

1. **Lỗi xác thực SSH trong Job Deploy (`ssh handshake failed: unable to authenticate`)**:
   - *Nguyên nhân*: Máy chủ Azure VM chưa được cập nhật Public SSH Key tương ứng với Private Key lưu trong GitHub Secrets.
   - *Giải quyết*: Sử dụng tính năng Run Command (`RunShellScript`) trên Azure Portal để tự động ghi Public Key vào `~/.ssh/authorized_keys` và thiết lập phân quyền `chmod 700/600` chuẩn Linux.

2. **Lỗi GitHub Push Protection bị từ chối Push**:
   - *Nguyên nhân*: File `scratch_setup_vm.sh` có chứa cứng chuỗi Connection String của Azure Storage và thư mục `mlruns/` chứa các file `.pkl` dung lượng lớn.
   - *Giải quyết*: Thêm `mlruns/` và `scratch_setup_vm.sh` vào `.gitignore`, thay thế chuỗi Secret Key bằng biến môi trường và thực hiện `git reset` commit sạch trước khi push lại.

3. **Lỗi định dạng JSON khi gọi API bằng `curl` trên Windows PowerShell**:
   - *Nguyên nhân*: PowerShell tự động tước bỏ dấu ngoặc kép khi truyền tham số cho `curl.exe`.
   - *Giải quyết*: Chuyển sang sử dụng cmdlet chuẩn `Invoke-RestMethod` của PowerShell kết hợp với `ConvertTo-Json` để gửi payload JSON chính xác.
