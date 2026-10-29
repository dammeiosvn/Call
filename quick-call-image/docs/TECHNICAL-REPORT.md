# Báo cáo mã nguồn và kiểm thử

**Dự án:** Quick Call Image · **Phiên bản:** 1.0.0-beta.2 · **Ngày:** 2026-10-29.

## Phản hồi thiết bị và bản sửa beta.2

Người dùng xác nhận đã cài cả hai tệp beta.1, chạy trực tiếp và từ bảng Chia sẻ
đều thấy cảnh báo cấu hình không hợp lệ. Ảnh cho thấy dừng tại kiểm tra metadata,
trước OCR; chưa có bằng chứng số điện thoại hay quyền camera là nguyên nhân.
Không công bố ảnh hoặc thông tin liên hệ trên hoá đơn của người dùng vào repo.

Beta.2 thay các literal `WFConditionalActionString` bằng String gốc và literal
`WFNumberValue` bằng Number gốc; chỉ dùng token/attachment khi có biến thật.
Mỗi cấp từ điển được đọc bằng một action với một khoá, không lệ thuộc dot-path.
Dot notation có hỗ trợ chính thức của Apple; thay đổi này nhằm cô lập đường đọc,
không có nghĩa Apple không hỗ trợ tính năng đó.

Kiểm tra dữ liệu nhúng trước I/O; lỗi metadata kèm mã nguồn B/L và giá trị thực tế.
Catalog JSON hợp lệ nhưng schema/engine không hỗ trợ được sao lưu và khôi phục,
giữ settings. Interpreter trước chấp nhận literal bọc token quá rộng; phiên bản
mới ràng buộc định dạng xuất và kiểm tra đường khôi phục/chẩn đoán.

Đây là bản sửa có mục tiêu theo bằng chứng hiện có. Chưa có giá trị metadata
thực tế từ iPhone tại điểm lỗi nên chưa chứng minh nguyên nhân duy nhất; cần
người dùng thử beta.2 để xác nhận lỗi khởi tạo đã hết.

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
| `src/sign_remote.py` | Ký bản nguồn công khai qua API Shortcuty; kiểm tra hash đầu vào/đầu ra, kích thước, AEA1 và mode anyone. Không nằm trong runtime iOS. |
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

- **21 phương thức kiểm thử đạt**, không lỗi/không bỏ qua trong lần chạy có oracle.
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

**Hai tệp phân phối đã được ký**, có đầu tệp AEA1, mode `anyone`, hash đầu vào,
hash đầu ra và kích thước khớp với phản hồi API. Kết quả nằm trong `qa/signing.json`.
Tệp đầu vào bplist đã được so sánh với graph XML trước khi gửi ký.

Máy macOS của GitHub Actions không đăng nhập iCloud nên cách ký CLI Apple đã
thất bại; bằng chứng lưu riêng trong `qa/signing-macos.json`. Sau đó sử dụng API
công khai không yêu cầu khoá của Shortcuty theo tài liệu nhà cung cấp. Chỉ mã
nguồn công khai của phím tắt được gửi đi, không có ảnh, số điện thoại đọc từ ảnh
hay cấu hình người dùng. CI có bước dự phòng này nếu máy ký thiếu phiên iCloud.

[Lượt kiểm thử CI ban đầu](https://github.com/dammeiosvn/Call/actions/runs/40805375624)
đạt bước validate; cần xem nội dung signing.json thay vì suy luận từ màu xanh của
job (bước thử ký CLI được cho phép thất bại để vẫn thu thập báo cáo).

**Beta.1 đã nhập được trên iPhone nhưng lỗi khởi tạo. Beta.2 chưa được thử lại.**
AEA1 và hash khớp là bằng chứng kiểm tra tệp phân phối, không phải bằng chứng
toàn bộ tác vụ đã thực thi trên iOS.

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
- [Shortcuty — API ký công khai](https://github.com/Shortcuty/Signing-Server-API-Documentation/blob/main/README.md)
