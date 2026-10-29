# Hướng dẫn Quick Call Image · beta.6

©️ Sentechtipsvn

## Sửa lỗi bản Gọi beta.5

Cài thay bản có chức năng gọi bằng beta.6, giữ thư mục QuickCall và các tệp hiện có.
Cảnh báo trong video xảy ra sau chọn ảnh; không đủ bằng chứng kết luận catalog
bị hỏng. Bản cũ dùng lại bộ nhận diện số trước Call và báo sai thành lỗi cấu hình.
Beta.6 bỏ bước đó, dùng số E.164 đã kiểm tra, chuyển sang kiểu Phone Number của iOS
rồi đưa chính biến đó vào Call. Bản Test mới cũng kiểm tra phép chuyển kiểu này.

- QC401: đích gọi không qua kiểm tra E.164.
- QC402: iOS không tạo được đúng một giá trị Phone Number từ đích đã kiểm tra.
- Hai mã này không yêu cầu xoá catalog. Gửi toàn bộ thông báo để chẩn đoán.

Nếu catalog beta.5 và settings còn hợp lệ, không cần thiết lập lại. Nếu trước đó
đã xoá riêng catalog, phím tắt tạo lại catalog nhưng giữ settings hợp lệ.
Một số hợp lệ sẽ chuyển sang gọi; nên thử với số có thể chủ động phối hợp kiểm tra.
Beta.6 vẫn chờ xác nhận cuộc gọi thật trên iPhone.

## Cài và cập nhật

Cài bản Test trước. Thay bản Test cũ để tránh chọn nhầm từ bảng Chia sẻ.
Giữ thư mục **iCloud Drive → Shortcuts → QuickCall**. Bản Test và bản có chức năng
gọi dùng chung cấu hình; bản Test không chứa tác vụ Gọi.

Beta.5 nâng engine dữ liệu lên 2 để nhận cả số cố định. Catalog cũ được giữ tại
`catalog.previous.json` trước khi khôi phục catalog mới. Quốc gia và ngôn ngữ trong
settings được giữ. Nếu từng sửa catalog, tham khảo bản sao để áp dụng lại thay đổi.

## Thiết lập lần đầu

1. Mở phím tắt, chọn quốc gia/vùng, ví dụ 🇻🇳 VN +84 · Việt Nam.
2. Chọn ngôn ngữ. Vùng số và ngôn ngữ độc lập với nhau.
3. Cho phép truy cập/lưu tệp khi iOS hỏi.
4. Sau khi lưu và đọc xác minh thành công, hiện:

> Đã cài đặt cấu hình phím tắt thành công. Bạn vui lòng chạy lại phím tắt.

Bấm OK để kết thúc rồi chạy lại. Nếu lần đầu chạy từ bảng Chia sẻ, chia sẻ lại
ảnh sau khi thiết lập. Lần sau không hỏi thiết lập khi settings còn hợp lệ.
Người đã có settings hợp lệ có thể đi thẳng vào menu, không thấy hộp thiết lập mới.
Hộp xin quyền của iOS vẫn do hệ thống hiển thị.

## Dùng bản Test

- Chọn Chụp ảnh, Chọn ảnh thư viện hoặc chia sẻ ảnh từ ứng dụng Ảnh.
- Chia sẻ nhiều ảnh: chọn một ảnh để đọc.
- Một số hợp lệ: hộp **Quick Call Image · Test** hiện số quốc tế đầy đủ, không gọi.
- Nhiều số: danh sách dạng `📞 0912345678 - Gọi`; chọn một dòng để xem số đích Test.
- Số thuộc vùng mặc định hiển thị dạng nội địa; số vùng khác giữ `+…`.
- Tên, địa chỉ và dòng văn bản OCR không xuất hiện trong hàng số.
- Không có số: chụp/chọn lại ảnh hoặc nhập/sửa số.

So sánh từng chữ số với ảnh gốc. Ví dụ VN `0912 345 678` thành `+84912345678`.
Số cố định cần đầy đủ mã vùng; số ngắn thiếu mã vùng không được tự đoán.
Một số lặp lại theo nhiều cách viết chỉ tính một lần.

## Bản có chức năng gọi

Chỉ thử sau khi Test hiện đúng số đích. Một số hợp lệ duy nhất thì chuyển sang
Gọi; nhiều số thì chọn. iOS có thể yêu cầu xác nhận hoặc chọn SIM/ứng dụng gọi.
Số ngoài 20 vùng hỗ trợ không được âm thầm ghép mã nước mặc định để gọi.

## Cài đặt và giới thiệu

Giữ các mục Chụp ảnh, Chọn ảnh thư viện, Cài đặt, Giới thiệu, Huỷ.
Giới thiệu hiện **Quick Call Image**, phiên bản, **©️ Sentechtipsvn** và mô tả.
Cài đặt cho phép đổi vùng/ngôn ngữ hoặc khôi phục dữ liệu gốc. Thay đổi cài đặt
được xác minh rồi thông báo đã lưu; không buộc thoát như thiết lập lần đầu.

## Xử lý lỗi

- QC301: không xác minh được metadata/các danh mục chính của catalog vừa lưu.
- QC302: một trường settings đọc lại khác lựa chọn đã lưu. Chưa báo thành công.
- QC202/203/204: lỗi điều hướng/menu/ánh xạ; gửi toàn bộ thông báo, không xoá catalog theo các mã này.
- QC201: giới hạn thao tác, kèm Pass/Limit/Route.
- JSON hỏng cú pháp có thể khiến tác vụ iOS dừng trước menu; giữ bản sao rồi xoá riêng tệp hỏng để thiết lập lại.
- OCR đọc sai: dùng ảnh rõ hơn hoặc nhập/sửa tay; đúng định dạng không chứng minh đúng người nhận cuộc gọi.

Beta.6 cần kiểm tra trên iPhone: thiết lập lần đầu, chạy lại, ảnh một số, ảnh nhiều
số, số cố định, Chia sẻ và Giới thiệu. Chưa chuyển sang phát hành cộng đồng chính thức.
