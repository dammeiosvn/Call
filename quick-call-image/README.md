# Quick Call Image · 1.0.0-beta.4

Phím tắt iOS đọc số điện thoại từ ảnh chụp, thư viện hoặc bảng Chia sẻ. Một số
hợp lệ sau chuẩn hoá và loại trùng thì chuyển sang tác vụ Gọi; nhiều số thì hiện
danh sách có icon để chọn. Giao diện dùng cách xưng hô cộng đồng, không cá nhân hoá.

**Trạng thái:** bản thử nghiệm. Beta.3 đã chạy vòng lặp nhưng báo QC202 với
Route rỗng ở lượt 2. Beta.4 lấy phần tử lặp theo chỉ số, chặn menu rỗng/lựa chọn
không ánh xạ và sửa thông báo lỗi nội bộ; đang chờ thử lại trên iPhone.
Chỉ tệp đã ký `Quick Call Image.shortcut` và `Quick Call Image Test.shortcut`
mới là bản cài. Các tệp `.unsigned.bplist` là đầu vào kỹ thuật, không phải bản cài iOS.
Xem [báo cáo kỹ thuật](docs/TECHNICAL-REPORT.md) và `qa/signing.json` để biết trạng thái chữ ký.

**Hai tệp beta.4 đã ký:**

- [Quick Call Image Test.shortcut](dist/Quick%20Call%20Image%20Test.shortcut) — chỉ hiện số đích, không gọi.
- [Quick Call Image.shortcut](dist/Quick%20Call%20Image.shortcut) — bản chính có tác vụ gọi.

Đã kiểm tra AEA1, mode anyone và hash tệp với phản hồi của dịch vụ ký. Bạn nên
thay bản cũ bằng beta.4 và bắt đầu bằng bản Test. Không cần xoá thư mục QuickCall.

- [Hướng dẫn sử dụng](docs/USER-GUIDE.md)
- [Báo cáo mã nguồn và kiểm thử](docs/TECHNICAL-REPORT.md)
- [Hướng dẫn sửa dữ liệu](docs/DATA-GUIDE.md)
- [Danh mục 20 vùng và 13 ngôn ngữ](config/catalog.json)
- [Kết quả kiểm thử có dữ liệu đầu vào/đầu ra](qa/test-results.json)
- [GitHub Actions](https://github.com/dammeiosvn/Call/actions/workflows/quickcall-ci.yml)

## Chức năng

- Thiết lập quốc gia/vùng và ngôn ngữ ở lần chạy đầu tiên.
- Lưu `settings.json`, `catalog.json` trong iCloud Drive → Shortcuts → QuickCall.
- Menu có emoji; nhãn, icon, thứ tự và bật/tắt mục lấy từ dữ liệu.
- Quốc gia mặc định và ngôn ngữ giao diện độc lập với nhau.
- Quy tắc số theo Google libphonenumber 9.0.42, nguồn được ghim tại commit
  `8593ab70fa4fadffc042b2714034f4c52bef7daf`.
- Chấp nhận số di động và dải cố định/di động dùng chung khi không phân biệt được.
- Chuẩn hoá số quốc tế, giữ đúng mã quốc gia, loại trùng trước khi đếm.
- Loại các trường mã đơn, mã số thuế, tiền có nhãn rõ ràng; cho nhập số khi OCR thất bại.
- Bản Test dùng cùng bộ xử lý nhưng **không chứa tác vụ Gọi**.
- Không có tác vụ mạng, trình duyệt, JavaScript, clipboard, gửi tin nhắn hoặc email
  trong phím tắt. iCloud Drive và cuộc gọi vẫn hoạt động theo cơ chế của iOS.

## Tạo lại từ nguồn

Python 3.10+; trình tạo không cần thư viện ngoài và không cần mạng:

```bash
python quick-call-image/src/catalog.py
python quick-call-image/src/build.py
```

Kiểm thử trên Linux/macOS có ICU:

```bash
python -m pip install -r quick-call-image/requirements-test.txt
python quick-call-image/tests/test_workflow.py
```

Để ký trên Mac có Shortcuts và quyền ký iCloud đang hoạt động:

```bash
python quick-call-image/src/sign_macos.py
```

Việc ký dùng `shortcuts sign --mode anyone`, theo tài liệu Apple. Chữ ký không
chứng minh OCR hoặc các tác vụ đã chạy đúng trên iPhone; vẫn cần bước thử thiết bị.

Nếu không có Mac đang đăng nhập iCloud, có thể dùng đường ký công khai ở bước phát triển:

```bash
python quick-call-image/src/sign_remote.py
```

Lệnh này gửi mã nguồn phím tắt công khai tới Shortcuty, kiểm tra hash rồi lưu tệp.
Đây chỉ là bước tạo bản phân phối; phím tắt iOS không liên hệ dịch vụ này khi chạy.

## Phạm vi xác minh

Đã kiểm tra graph plist đã xuất, luồng với camera/ảnh/tệp/cuộc gọi mô phỏng,
cú pháp và hành vi regex bằng ICU của máy chạy kiểm thử, cùng đối chiếu độc lập
với thư viện phonenumbers. Chưa đo độ chính xác OCR, tốc độ, hiển thị menu, quyền
tệp, chọn SIM hoặc hộp thoại gọi trên iOS thật. Không tuyên bố hỗ trợ toàn bộ
số cố định, tổng đài, số khẩn cấp, số bị che hoặc mọi ngôn ngữ OCR.

## Giấy phép

Mã dự án: MIT. Metadata và regex dẫn xuất: Apache-2.0, giữ thông báo nguồn trong `vendor/`.

Ảnh mẫu và đầu vào plist chưa ký có trong [QuickCall-Source.zip](https://github.com/dammeiosvn/Call/raw/refs/heads/main/quick-call-image/dist/QuickCall-Source.zip).
