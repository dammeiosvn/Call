# Quick Call Image · 1.0.0-beta.6

©️ Sentechtipsvn

Phím tắt iOS đọc số điện thoại từ camera, thư viện hoặc bảng Chia sẻ. Hỗ trợ số
cố định và di động theo dữ liệu 20 vùng; chuẩn hoá mã quốc gia và loại trùng.

**Trạng thái:** beta.5 Test đã được xác nhận chạy trên iPhone, nhưng bản Gọi báo
nhầm lỗi cấu hình sau chọn ảnh. Beta.6 bỏ lần nhận diện số thừa trước Call, dùng
chung phép chuyển kiểu số iOS ở cả Test và Gọi, thêm QC401/QC402. Đang chờ thử lại.

**Nguồn beta.6 đã cập nhật; bản cài beta.6 đang chờ ký. Các tệp dist còn là beta.5.**

## Bản cài

- [Quick Call Image Test.shortcut](dist/Quick%20Call%20Image%20Test.shortcut): chỉ hiện số đích, không chứa tác vụ Gọi.
- [Quick Call Image.shortcut](dist/Quick%20Call%20Image.shortcut): một số thì gọi, nhiều số thì chọn. Chỉ thử sau khi Test trả đúng số.
- [QuickCall-Source.zip](dist/QuickCall-Source.zip): mã nguồn, dữ liệu, báo cáo và ảnh mẫu.

Chỉ cài tệp đã ký; các tệp unsigned là đầu vào kỹ thuật.

## Luồng hiện tại

1. Lần đầu chọn quốc gia/vùng và ngôn ngữ, lưu JSON vào Shortcuts/QuickCall.
2. Đọc lại để xác minh; báo thiết lập thành công rồi kết thúc. Người dùng chạy lại.
3. Chụp/chọn/chia sẻ ảnh. Lọc và chuẩn hoá từng số, loại trùng trước khi đếm.
4. Menu dạng `📞 0912345678 - Gọi`. Số nước khác giữ mã quốc tế; ID đích luôn là E.164.
5. Giữ Cài đặt, Giới thiệu có tên phiên bản và tác giả, Huỷ, nhập/sửa số và thử ảnh khác.

Dữ liệu gồm 20 vùng, 13 ngôn ngữ và icon emoji. Runtime không dùng mạng,
trình duyệt, JavaScript hoặc gửi dữ liệu OCR; iCloud và gọi do iOS quản lý.

## Tài liệu và kiểm thử

- [Hướng dẫn sử dụng](docs/USER-GUIDE.md)
- [Báo cáo mã nguồn](docs/TECHNICAL-REPORT.md)
- [Hướng dẫn dữ liệu](docs/DATA-GUIDE.md)
- [Kết quả kiểm thử](qa/test-results.json), [đối chiếu độc lập](qa/oracle.json), [chữ ký](qa/signing.json)

33 phương thức host đạt, 209 kịch bản số đạt và 1.640 đối chiếu với phonenumbers
9.0.42 đạt. Đây là kiểm thử graph với I/O mô phỏng, không phải xác nhận thiết bị.

## Tạo lại

```bash
python quick-call-image/src/catalog.py
python quick-call-image/src/build.py
python -m pip install -r quick-call-image/requirements-test.txt
python quick-call-image/tests/test_workflow.py
```

Ký trên Mac có phiên iCloud: `python quick-call-image/src/sign_macos.py`.
Có thể ký nguồn công khai bằng `python quick-call-image/src/sign_remote.py`.
Lệnh sau gửi đầu vào phím tắt đến API Shortcuty; không gửi ảnh hay cấu hình thiết bị.

Mã nguồn MIT; metadata và regex dẫn xuất Apache-2.0, giữ thông báo trong vendor/.
