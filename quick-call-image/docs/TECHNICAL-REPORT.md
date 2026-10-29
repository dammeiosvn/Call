# Báo cáo mã nguồn · Quick Call Image 1.0.0-beta.6

©️ Sentechtipsvn · 2026-10-29

## Bằng chứng thiết bị và bản sửa beta.6

Người dùng đã xác nhận beta.5 Test: setup thành công, nguồn thư viện/Chia sẻ,
menu gọn, số E.164 ở hộp kết quả khớp số trong ảnh. Hai video bản Gọi cho thấy:
trước xoá catalog báo lỗi cấu hình; sau xoá có thể setup thành công, chạy lại và
chọn ảnh nhưng vẫn báo lỗi cấu hình. Không có mã QC101/102/301/302 trong cảnh báo
sau chọn ảnh. Đây không phải bằng chứng catalog đọc không được.

Source beta.5 có hai nhánh cuối riêng: Test chỉ hiện DialTarget, còn Call chạy
Get Phone Numbers from Input lần nữa và đòi Count=1; nếu không đạt thì hiện
invalidConfig có lời khuyên xoá catalog. Hành vi này giải thích một lỗi báo nhầm
phù hợp video. Video không cho biết đầu ra detector thực tế; chưa đo được giá trị
đó trên iPhone nên không tuyên bố riêng lỗi bên trong detector đã được chứng minh.

Beta.6 bỏ hẳn lần dò số tự do đó. Cả hai bản cùng thực hiện:
E.164 validation → Set PhoneTarget với WFPhoneNumberContentItem coercion → Count=1.
Test hiện đích đã kiểm tra; Call nhận biến PhoneTarget trực tiếp qua WFCallContact.
Giữ IntentAppDefinition của Phone. Không cắt số từ nhãn, không ghép mã nước lần hai.
Đích không hợp lệ báo QC401; chuyển kiểu thất bại báo QC402. Không hướng dẫn xoá
catalog cho hai lỗi này. Mọi nhánh thoát sau khi gọi/hiện Test, không gọi lần hai.

Mô phỏng pipeline cũ với detector trả 0 hoặc 2 giá trị tái hiện cảnh báo catalog
sai; bản mới không chứa detect.phonenumber, nên không phụ thuộc đầu ra detector.
Kiểm thử thêm cùng cached catalog beta.5, giữ settings, bỏ riêng catalog rồi dựng
lại, đường nhiều số và chuyển kiểu iOS thất bại ở cả Test/Call.

33 phương thức host đạt, 209 kịch bản số và 1.640 đối chiếu đạt. Coercion iOS được
mô phỏng bằng hợp đồng kiểu; không phải xác nhận native conversion hoặc Phone
intent đã chạy trên thiết bị. Cần người dùng thử beta.6. Không đưa ảnh/video/số
liên hệ thực của người dùng vào repo.

Tham khảo cấu trúc Call nhận biến: [Cherri contacts.cherri](https://github.com/electrikmilk/cherri/blob/main/actions/contacts.cherri).

## Thay đổi beta.5

- Đọc lại JSON và kiểm tra dữ liệu sau giải mã, thay so sánh hash chuỗi. iOS có thể
  thay cách biểu diễn JSON mà không đổi dữ liệu; đây là nguyên nhân có thể của
  saveFailed, chưa xác nhận duy nhất từ thiết bị. Không đổi lỗi thành thành công.
- Catalog vừa ghi: kiểm tra schema, engine, phiên bản và số lượng countryOrder,
  languageOrder, countries, languages. Đây là kiểm tra trường bắt buộc, không phải
  chứng minh toàn bộ từng leaf của catalog khớp byte. Settings: kiểm tra cả bốn
  trường schemaVersion, region, language, singleResult.
- Thiết lập lần đầu chỉ báo thành công sau xác minh, rồi Exit. Không OCR/gọi trong
  lượt thiết lập, kể cả nhận ảnh Chia sẻ; người dùng chạy/chia sẻ lại.
- Menu số không kèm dòng OCR. Numbers chỉ lưu E.164 → "1" để loại trùng.
  Hàng hiển thị có icon, dạng nội địa khi hợp lệ theo vùng mặc định, dấu " - " và
  nhãn call đã dịch; ánh xạ SHA256 của hàng sang E.164, không tách số từ nhãn.
- Số nước khác giữ E.164. US/CA dùng cùng +1 nhưng chỉ chuyển dạng nội địa nếu
  NSN khớp profile của vùng mặc định. Prefix lấy từ dữ liệu, giữ số là Text.
- Bản Test dùng Text → Set Variable → Show Alert, hiện E.164 đầy đủ, không có Call.
  Thay Show Result vì video cho thấy phần số bị thiếu khi hiển thị.
- Giữ menu Giới thiệu; tên/phiên bản và author lấy từ nguồn hiện tại. Bổ sung nhãn
  còn thiếu từ bản dịch nhúng mà không ghi đè nhãn tuỳ chỉnh có sẵn.
- Hỗ trợ FIXED_LINE, MOBILE và FIXED_LINE_OR_MOBILE trong 20 vùng. Regex là hợp
  độ dài và mẫu của từng loại, giao với generalDesc. Không nhận localOnly, tổng
  đài dịch vụ, số khẩn cấp hoặc sửa chữ số OCR theo suy đoán.
- Engine 2 buộc thay catalog engine 1 bằng bản mới, có catalog.previous.json và
  giữ settings. JSON lỗi cú pháp vẫn có thể dừng tác vụ trước nhánh khôi phục.

## Kiến trúc và tái tạo

| Tệp | Vai trò |
|---|---|
| src/catalog.py | Trích snapshot libphonenumber, ghép 20 vùng, bản dịch và menu. |
| src/workflow.py | Xuất plist xác định, UUID, token UTF-16, điều kiện và vòng lặp. |
| src/build.py | File/config, menu, OCR, chuẩn hoá, loại trùng, Test hoặc Call. |
| src/sign_macos.py | Thử ký CLI Apple mode anyone. |
| src/sign_remote.py | Ký nguồn công khai qua Shortcuty, kiểm tra input/output hash, size, AEA1. |
| tests/interpreter.py | Chạy graph đã xuất với I/O mô phỏng. |
| tests/icu.py | Chạy ICU của host. |
| tests/test_workflow.py | Kiểm thử hành vi, wire shape và oracle độc lập. |

Không dùng mạng/webview/JS/clipboard/gửi tin trong runtime. iCloud và cuộc gọi do
hệ điều hành quản lý. Mỗi bản tự hoạt động, không cần phím tắt phụ. Vòng each chụp
list vào biến riêng và lấy item theo Repeat Index với toàn bộ độ sâu lặp; không
phụ thuộc tên Repeat Item. Guards QC203/204 dừng menu rỗng/không ánh xạ ngay tại nguồn.

## Kiểm thử

33 phương thức đạt, 209 kịch bản số đạt, 1.640 đối chiếu với phonenumbers 9.0.42
đạt. Không bỏ qua oracle. Bao gồm 20 mẫu số cố định, tất cả trường hợp trước,
khôi phục catalog engine 1, JSON đổi thứ tự/whitespace, settings đọc sai không
báo thành công, thiết lập dừng không OCR, menu gọn, ngoại vùng giữ +CC và tác giả.

Snapshot ghim commit 8593ab70fa4fadffc042b2714034f4c52bef7daf của Google; mã dự án
MIT, metadata và regex dẫn xuất Apache-2.0. SHA snapshot trong config/catalog.json.
Báo cáo qa/build.json, test-results.json, oracle.json, device-feedback.json và
signing.json lưu bằng chứng từng phần; chữ ký không chứng minh đúng chức năng.

## Trước phát hành chính thức

Phải thử beta.5 trên iPhone: setup/rerun, quyền tệp, camera/thư viện/Chia sẻ, số
đích Test một/nhiều số, số cố định, huỷ/nhập sửa và About. Sau đó thử bản Call
với số do người kiểm thử chủ động liên hệ. Chưa có kết quả thiết bị beta.5.

Nguồn: [Google metadata](https://github.com/google/libphonenumber/tree/8593ab70fa4fadffc042b2714034f4c52bef7daf),
[Apple Repeat](https://support.apple.com/guide/shortcuts/use-repeat-actions-apdc11deb2c1/ios),
[Apple ký CLI](https://support.apple.com/guide/shortcuts-mac/run-shortcuts-from-the-command-line-apd455c82f02/mac),
[Shortcuty signing API](https://github.com/Shortcuty/Signing-Server-API-Documentation).

## Trạng thái phân phối beta.6

Nguồn và kiểm thử đã hoàn tất, bản cài mới đang chờ ký. Báo cáo ký beta.5 giữ
riêng tại qa/signing-beta5.json. Không gắn lại nhãn beta.5 thành beta.6. Ký sẽ dùng
nguồn đã công khai; chữ ký không thay thế bước xác minh cuộc gọi thật.
