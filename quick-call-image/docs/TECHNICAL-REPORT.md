# Báo cáo mã nguồn và kiểm thử

**Dự án:** Quick Call Image · **Phiên bản:** 1.0.0-beta.1 · **Ngày:** 2026-10-29.

## Kết quả triển khai

Đã tạo trình biên dịch sinh graph Apple Shortcuts native, bản chính và bản Test,
dữ liệu 20 vùng/13 ngôn ngữ, quy tắc chuẩn hoá, menu lấy từ dữ liệu, thiết lập lần
đầu, lưu JSON và hướng dẫn sử dụng. Runtime không có mạng, trình duyệt hay JavaScript.

**Bản beta chưa được chứng nhận chạy trên iPhone thật.** Tình trạng chữ ký tệp
được ghi riêng tại `qa/signing.json`. Chỉ tệp đã ký mới cài được trên iOS; tệp
`.unsigned.bplist` là đầu vào để ký và kiểm tra mã nguồn.

## Kiến trúc

| Tệp | Trách nhiệm |
|---|---|
| `src/catalog.py` | Đọc snapshot metadata, trích 20 vùng, ghép bản dịch/icon/menu, xuất catalog. |
| `src/workflow.py` | Xuất UUID xác định, token UTF-16, tham chiếu biến, điều kiện và vòng lặp native. |
| `src/build.py` | Thiết lập, đọc/ghi JSON, OCR, chuẩn hoá, loại trùng, chọn số và nhánh gọi. |
| `src/sign_macos.py` | Ký bằng CLI Apple ở chế độ anyone, có timeout và kiểm tra đầu tệp AEA1. |
| `tests/interpreter.py` | Thực thi graph plist đã xuất với I/O giả, phát hiện biến/tham chiếu không được gán. |
| `tests/icu.py` | Chạy regex theo ICU C API của host; không thay thế kiểm thử ICU trên iOS. |
| `tests/test_workflow.py` | Kiểm thử số, điều khiển, tệp, cấu hình, bản dịch và đối chiếu độc lập. |

Mỗi phím tắt tự hoạt động, không gọi phím tắt phụ bằng tên. Bản Test được tạo từ
cùng hàm biên dịch, thay nhánh gọi bằng Hiển thị kết quả. Trong bản Test không có
identifier `com.apple.mobilephone.call`.

## Luồng dữ liệu

1. Giữ ảnh Chia sẻ trước khi hiển thị bất kỳ menu thiết lập nào.
2. Nạp catalog cục bộ; nếu thiếu thì ghi dữ liệu nhúng và kiểm tra hash đọc lại.
3. Kiểm tra settings. Tệp thiếu/sai các trường hỗ trợ dẫn đến chọn vùng và ngôn ngữ.
4. Lưu JSON, kiểm tra hash đọc lại rồi mới thông báo thành công.
5. Nhận một ảnh; nhiều ảnh đầu vào thì chọn một. Camera/thư viện dùng tác vụ iOS.
6. OCR thành văn bản; chuyển các chữ số Unicode tương đương, tách từng dòng.
7. Tìm từng cụm số. Không nối toàn bộ chữ số trên hoá đơn.
8. Bỏ qua nhãn rõ ràng của mã số thuế, đơn hàng, tài khoản hoặc tiền. Đây là heuristic, không phải hiểu tài liệu hoàn hảo.
9. Số nội địa dùng vùng mặc định; số có mã quốc tế được xét trong 20 vùng hỗ trợ.
10. Kiểm tra NSN toàn chuỗi, tạo E.164 và kiểm tra lại giới hạn; loại trùng theo E.164.
11. Một số hợp lệ và không còn số quốc tế chưa hỗ trợ: gọi/hiện kết quả Test.
12. Nhiều số hoặc còn trường quốc tế chưa xử lý: chọn rõ số đích trong menu.

Regex nguồn lấy từ libphonenumber 9.0.42, commit
`8593ab70fa4fadffc042b2714034f4c52bef7daf` (2026-10-22). Snapshot gốc được nén gzip
không mất dữ liệu; SHA-256 bản giải nén nằm trong `catalog.meta.metadataSHA256`.
Phần nhập số hỗ trợ tập quy tắc được nêu ở đây, không phải bản cài toàn bộ thư viện Google.

## Bằng chứng kiểm thử host

- **17 phương thức kiểm thử đạt**, không lỗi/không bỏ qua trong lần chạy có oracle.
- **189 kịch bản số điện thoại đạt**, lưu chi tiết input/expected/actual tại `qa/test-results.json`.
- **1.620 phép so sánh** mẫu số với `phonenumbers==9.0.42` đạt, gồm mẫu nguồn và số giả sinh xác định.
- Đối chiếu chỉ tính số canonical: parser Google có thể tự bỏ tiền tố sau `+CC`,
  còn lõi này yêu cầu dạng chính xác hoặc dấu `(0)` được chỉ rõ.
- Đã kiểm tra thiết lập mới, chạy lại không ghi dư, đổi vùng/ngôn ngữ, khôi phục
  cấu hình, huỷ, lỗi lưu, nguồn camera/ảnh/Chia sẻ, nhiều ảnh, nhập sửa số.
- Đã kiểm tra đổi tên có dấu chấm, đổi emoji, đảo thứ tự và tắt mục menu mà vẫn đi đúng handler.
- Đã kiểm tra đủ khoá của 13 bản dịch, nhãn không trùng trong menu và không có xưng hô cá nhân.
- Đã kiểm tra UUID duy nhất, tham chiếu action trỏ về trước, vị trí token theo UTF-16,
  plist tạo lại đúng nguồn và không có tác vụ mạng/web/clipboard/gửi tin.

Các số và ảnh mẫu là dữ liệu minh hoạ. I/O trong interpreter được mô phỏng;
`destinations` là ghi nhận đích dự kiến, không phải cuộc gọi được thực hiện.

## Chữ ký và giới hạn xác minh

Ký tệp khác với xác minh tác vụ. `shortcuts sign` có thể ký một plist nhưng không
chứng minh mọi thông số chạy đúng trên iOS. Quy trình ký dùng mode `anyone`,
kiểm tra AEA1 và hash; không tạo hoặc giả mạo liên kết chia sẻ iCloud.

Kênh ký trực tiếp từ môi trường phát triển hiện bị chặn HTTP 403. Workflow GitHub
Actions có bước thử ký bằng macOS và lưu kết quả; runner có thể không có phiên
iCloud đủ quyền. Nếu `qa/signing.json` ghi `signed: false`, **chưa có bản cài**.

Trình validator cũ còn trong môi trường trước không có catalog action đi kèm và
báo unknown cho cả action chuẩn; kết quả đó không được dùng làm chứng nhận.
Dự án dùng kiểm tra cấu trúc/tham chiếu của graph và interpreter riêng, cộng với
schema tham số đã đối chiếu từ catalog action có sẵn và mã nguồn Cherri.

## Những phần phải thử trên iPhone

1. Nhập tệp đã ký, menu có icon và tham chiếu lồng trong vòng lặp hoạt động đúng.
2. Thư mục Shortcuts biểu tượng chung được iOS phân giải đúng, quyền tệp và lưu JSON hoạt động.
3. Chụp ảnh/chọn thư viện/Chia sẻ, OCR thực tế và từng chữ số nhận được.
4. Hiệu năng với ảnh hoá đơn thật, menu ngôn ngữ dài, ký tự Khmer/Lào/Thái.
5. Chọn SIM, ứng dụng gọi mặc định, hộp thoại hệ thống và đích gọi thật.
6. Cập nhật catalog, lỗi file provider và JSON hỏng trên iOS.

Chưa đo thời gian hay phần trăm chính xác. Chưa có kết quả OCR trên iPhone thật,
chưa đặt cuộc gọi thật. Không suy diễn kết quả host thành kết quả thiết bị.

## Giới hạn sản phẩm hiện tại

- Chỉ 20 vùng được bật; số quốc tế ngoài phạm vi được giữ trạng thái chưa hỗ trợ.
- Chủ yếu số di động; dải cố định/di động dùng chung ở US/CA được chấp nhận.
- Không gọi số khẩn cấp, tổng đài dịch vụ hoặc số thiếu chữ số thuê bao theo suy đoán.
- VN và các vùng yêu cầu tiền tố nội địa không tự khôi phục số `0` bị mất.
- Không tự sửa O/I thành 0/1. Đúng mẫu không chứng minh đúng người hoặc số đang hoạt động.
- Nếu JSON catalog hỏng cú pháp, tác vụ iOS có thể dừng trước menu lỗi; xoá tệp
  bị hỏng để khởi tạo lại. Settings dùng bộ kiểm tra JSON phẳng trước khi giải mã.
- Icon menu là emoji, không phải ảnh PNG/vCard. Chưa có cập nhật GitHub tự động.
- Camera và quyền hệ thống phải hiển thị theo iOS; chuỗi do hệ thống tạo không nằm trong gói bản dịch.

## Điều kiện chuyển sang phát hành cộng đồng

Phải có hai tệp ký hợp lệ, nhập và chạy bản Test trên iPhone mục tiêu, kiểm tra
số đích bằng ảnh thật, rồi thử bản chính bằng số được người kiểm thử chủ động
chọn. Phản hồi lỗi phải được xử lý trước khi đổi trạng thái khỏi beta.

Nguồn:

- [Google metadata đã ghim](https://github.com/google/libphonenumber/blob/8593ab70fa4fadffc042b2714034f4c52bef7daf/resources/PhoneNumberMetadata.xml)
- [Google FAQ về chuẩn hoá và loại số](https://github.com/google/libphonenumber/blob/8593ab70fa4fadffc042b2714034f4c52bef7daf/FAQ.md)
- [ITU National Numbering Plans](https://www.itu.int/oth/t0202)
- [Apple — ký từ dòng lệnh](https://support.apple.com/guide/shortcuts-mac/run-shortcuts-from-the-command-line-apd455c82f02/mac)
- [Cherri — Phone actions](https://github.com/electrikmilk/cherri/blob/main/actions/contacts.cherri)
