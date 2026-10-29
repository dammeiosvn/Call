# Hướng dẫn sử dụng Quick Call Image

Phiên bản 1.0.0-beta.2. Khuyến nghị thử trên iOS 18 trở lên. Beta.1 đã được cài
trên iPhone nhưng dừng ở bước kiểm tra cấu hình. Beta.2 đang chờ thử lại; kết quả
mô phỏng không thay thế bước thử thiết bị.

## Cập nhật từ beta.1 bị lỗi cấu hình

1. Thay hai phím tắt cũ bằng hai tệp beta.2 mới; nếu iOS thêm bản trùng tên, xoá
   riêng hai phím tắt beta.1 để tránh chạy nhầm từ bảng Chia sẻ.
2. Chưa cần xoá thư mục QuickCall hoặc các tệp cấu hình.
3. Mở **Quick Call Image Test** trực tiếp trong Phím tắt lần đầu. Nếu chưa có
   cài đặt, bạn sẽ được chọn quốc gia/vùng và ngôn ngữ rồi cấp quyền lưu tệp.
4. Chọn ảnh hoặc chia sẻ một ảnh để kiểm tra số đích.
5. Nếu vẫn báo lỗi, chụp trọn thông báo có mã `QC101-B`, `QC102-B`, `QC101-L`
   hoặc `QC102-L` và giá trị Actual/Expected. Không sửa điều kiện thủ công.

Mã đuôi `B` chỉ dữ liệu nhúng, `L` chỉ dữ liệu nạp. Lỗi dữ liệu nhúng không phải
bằng chứng tệp của bạn bị hỏng. Catalog có JSON hợp lệ nhưng schema/engine không
tương thích sẽ được sao lưu vào `catalog.previous.json` rồi khôi phục từ bản
nhúng; cài đặt quốc gia/ngôn ngữ vẫn giữ. JSON sai cú pháp vẫn cần xử lý như mục 6.

## 1. Chọn đúng tệp để cài

Tệp cài, sau khi ký thành công, nằm trong `dist/`:

- **Quick Call Image Test.shortcut**: hiện số đích, không gọi.
- **Quick Call Image.shortcut**: một số hợp lệ thì chuyển sang tác vụ Gọi.

Chỉ tải tệp đã ký. `.unsigned.bplist` và tệp XML sinh từ mã nguồn là dữ liệu kỹ
thuật, không nhập trực tiếp được trên iOS hiện đại. Trạng thái ký được ghi tại
`qa/signing.json` hoặc trong artifact `QuickCall-native-signing` của GitHub Actions.

Đã có hai tệp ký trong `dist/`. Đầu tệp AEA1, mode anyone, hash và kích thước đã
được kiểm tra; việc nhập và chạy trên iPhone đang chờ người dùng thử nghiệm.

Mở tệp đã tải bằng ứng dụng Phím tắt và chọn thêm phím tắt. Tệp được ký ở chế độ
`anyone`, không yêu cầu lưu người tạo vào danh bạ. Chữ ký không phải chứng nhận
chức năng đã hoạt động trên thiết bị của bạn.

## 2. Thiết lập lần đầu

1. Mở **Quick Call Image Test** trước.
2. Chọn quốc gia/vùng, ví dụ **🇻🇳 VN +84 · Việt Nam**.
3. Chọn ngôn ngữ, ví dụ **Tiếng Việt**. Bạn có thể dùng tiếng Việt cùng bất kỳ vùng số nào.
4. Cho phép truy cập thư mục Tệp khi iOS hỏi. Phím tắt tạo **iCloud Drive → Shortcuts → QuickCall**.
5. Chỉ khi lưu và đọc kiểm tra thành công mới hiện thông báo đã lưu.

Các tệp `settings.json` và `catalog.json` được dùng chung giữa bản chính và bản
Test. Lần sau không phải chọn lại. Tệp có thể được iCloud đồng bộ; trước khi dùng
ở vùng khác, bạn hãy kiểm tra quốc gia mặc định trong Cài đặt.

Nếu lần đầu chạy từ bảng Chia sẻ, phím tắt vẫn giữ ảnh đã nhận và xử lý ảnh đó
sau khi thiết lập xong. Nếu huỷ thiết lập, không có cuộc gọi nào được thực hiện.

## 3. Chọn ảnh

- **📸 Chụp ảnh**: mở camera sau, chụp một ảnh.
- **🖼️ Chọn ảnh thư viện**: chọn một ảnh có số điện thoại.
- Trong ứng dụng Ảnh: mở ảnh → **Chia sẻ** → chọn phím tắt. Nếu không thấy,
  kiểm tra mục **Hiển thị trong bảng Chia sẻ** trong chi tiết phím tắt.
- Nội dung trong ứng dụng khác có thể được đưa vào bằng ảnh chụp màn hình.
- Nếu Chia sẻ nhiều ảnh, bạn chọn một ảnh; chỉ ảnh được chọn mới được đọc.

Nên chụp rõ vùng số, đủ sáng, không cắt mất chữ số. Các ảnh mẫu trong
`tests/fixtures/` chỉ dùng với **bản Test**: đó là dữ liệu minh hoạ, không phải
thông tin liên hệ để gọi thật.

## 4. Kết quả

- **Không có số phù hợp:** chọn chụp lại, chọn ảnh khác, nhập số hoặc huỷ.
- **Một số hợp lệ duy nhất:** bản Test hiện số đích; bản chính chuyển sang Gọi.
- **Nhiều số:** hiện danh sách có icon, số quốc tế và dòng ngữ cảnh. Bạn chọn số
  nào thì dùng đúng số đó. Có thêm Nhập/sửa số, Chọn nguồn khác và Huỷ.
- Các dạng trùng nhau như `0912345678` và `+84912345678` chỉ tính một số.
- Nếu ảnh còn số quốc tế chưa hỗ trợ, bản chính không âm thầm bỏ số đó để tự
  gọi số còn lại: danh sách yêu cầu bạn chọn rõ số đích.

Ví dụ Việt Nam: `0912 345 678` → `+84912345678`. Không ghép thành `+840912…`.
Số có `+81…` được kiểm tra theo Nhật Bản dù bạn đang chọn Việt Nam.

Bản chính có thể gọi ngay sau OCR. Chỉ chuyển sang bản chính khi bạn đã thử bản
Test và hiểu kết quả. Hộp thoại hệ thống, ứng dụng gọi mặc định và lựa chọn SIM
phụ thuộc iPhone của bạn; phím tắt không vượt qua các xác nhận của iOS.

## 5. Cài đặt và cập nhật dữ liệu

- **⚙️ Cài đặt → 🌍 Quốc gia/vùng:** chọn vùng và ngôn ngữ rồi lưu.
- **⚙️ Cài đặt → 🌐 Ngôn ngữ:** đổi riêng ngôn ngữ, giữ vùng số.
- **⚙️ Cài đặt → ♻️ Khôi phục dữ liệu gốc:** ghi lại catalog đi kèm bản phím tắt
  hiện tại; giữ lựa chọn quốc gia và ngôn ngữ.
- Sau khi cài bản cập nhật có dữ liệu mới, dùng **Khôi phục dữ liệu gốc** để áp
  dụng catalog đi kèm. Không tải GitHub ở mỗi lần đọc ảnh.
- Người dùng nâng cao có thể đổi `singleResult` từ `"call"` sang `"choose"` trong
  `settings.json` để luôn hiện danh sách. Giữ giá trị các trường dạng chuỗi.

## 6. Xử lý lỗi

| Hiện tượng | Cách xử lý |
|---|---|
| Không thêm được phím tắt | Kiểm tra đó là tệp đã ký; không dùng `.unsigned.bplist` hoặc XML. |
| Hỏi thiết lập mỗi lần | Kiểm tra quyền và việc lưu `QuickCall/settings.json`; thử chạy trong Phím tắt khi máy đang mở khoá. |
| Báo không đọc được JSON | Trong Tệp, giữ bản sao nếu cần rồi xoá tệp bị hỏng trong QuickCall và chạy lại. JSON sai cú pháp có thể làm tác vụ iOS dừng trước khi menu phục hồi hiện ra. |
| Mã quốc gia không đúng | Đổi vùng mặc định; vùng này chỉ áp dụng cho số chưa có mã quốc gia. |
| Không nhận số thiếu tiền tố nội địa | Dùng dạng đầy đủ như `0912…` hoặc `+84912…`; bản này không tự đoán số `0` bị mất ở Việt Nam. |
| Chỉ đọc sai một chữ số | Dùng ảnh rõ hơn hoặc nhập/sửa tay. Đúng định dạng chưa chứng minh OCR đúng. |
| Không có số sau khi đọc | Kiểm tra vùng, loại số và chất lượng ảnh; tổng đài, số khẩn cấp, số bị che không nằm trong phạm vi bản này. |
| Tệp iCloud chưa có trên máy | Mở Tệp và tải tệp về trước; kết nối iCloud phụ thuộc thiết bị. |

## 7. Gửi phản hồi thử nghiệm

Ghi phiên bản iOS, tên bản Test/bản chính, vùng số, ngôn ngữ, nguồn ảnh, số bạn
mong đợi, số đích nhận được và màn hình lỗi. Bạn có thể che dữ liệu không liên
quan trên ảnh; giữ rõ vùng số để tái hiện lỗi. Với cuộc gọi thật, chỉ dùng số bạn
có chủ đích liên hệ.

Nguồn: [Apple — Chia sẻ phím tắt](https://support.apple.com/guide/shortcuts/share-shortcuts-apdf01f8c054/ios),
[Apple — ký bằng dòng lệnh](https://support.apple.com/guide/shortcuts-mac/run-shortcuts-from-the-command-line-apd455c82f02/mac).

Ảnh mẫu và đầu vào plist chưa ký có trong [QuickCall-Source.zip](https://github.com/dammeiosvn/Call/raw/refs/heads/main/quick-call-image/dist/QuickCall-Source.zip).
