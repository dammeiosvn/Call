# Sửa dữ liệu và mở rộng

## Nguồn chuẩn

| Thành phần | Sửa ở đâu |
|---|---|
| Câu chữ 13 ngôn ngữ | `config/languages.json` |
| Vùng, thứ tự, icon, menu, chính sách nhận số | `src/catalog.py` rồi tạo lại `config/catalog.json` |
| Regex quốc gia | Dữ liệu `vendor/PhoneNumberMetadata.xml.gz`, ghim commit nguồn; trình tạo trích phần cần dùng. |
| Luồng và chức năng native | `src/build.py` và lớp xuất plist `src/workflow.py` |
| Tuỳ chọn của người dùng | Tệp `QuickCall/settings.json` trên thiết bị |

`config/catalog.json` là toàn bộ từ điển dữ liệu đã biên dịch; có thể sửa trực
tiếp để nạp trên thiết bị, nhưng chạy lại `catalog.py` sẽ tạo lại tệp từ các nguồn
ở trên. Dữ liệu nhúng trong phím tắt dùng để khởi tạo/khôi phục. Khi đã có tệp,
runtime dùng catalog trên thiết bị. Không có cập nhật mạng tự động.

## Trường chính

- `meta.schemaVersion` và `meta.engineRevision`: hiện là chuỗi `"1"`.
- `countryOrder`, `languageOrder`: danh sách có thứ tự; không dựa vào thứ tự khoá.
- `countries.<ISO>.callingCode`: văn bản, ví dụ `"+84"`.
- `countries.<ISO>.nationalPrefix`: văn bản, có thể rỗng; không phải nước nào cũng dùng `0`.
- `countries.<ISO>.acceptBareNSN`: `"1"` cho phép dạng NSN không tiền tố nội địa;
  `"0"` yêu cầu tiền tố nội địa đối với số chưa có mã quốc gia. VN mặc định `"0"`.
- `countries.<ISO>.nationalPattern`: kiểm tra toàn bộ NSN, giao của độ dài,
  mẫu số chung và dải di động. Dải cố định/di động dùng chung được ghi rõ trong `numberType`.
- `countries.<ISO>.internationalPrefixPattern`: tiền tố gọi quốc tế theo vùng nguồn; không coi `00` là mặc định toàn cầu.
- `languages.<code>`: đầy đủ các khoá bằng gói `en`; tên ngôn ngữ dùng cách tự gọi.
- `icons`: emoji cho menu và kết quả; bản này chưa có bộ hiển thị icon PNG/vCard.
- `menus.<group>`: danh sách `{id, labelKey, iconKey, handler, enabled}`;
  `enabled` dùng chuỗi `"1"` / `"0"` để không lệ thuộc cách iOS hiển thị Boolean.
- `behavior`: mẫu tìm cụm số, bỏ qua trường mã đơn/thuế/tiền có nhãn và các giới hạn.
- `digitMap`: chuyển chữ số Unicode tương đương sang ASCII. Không sửa nhầm OCR như O/I thành 0/1.

Các mã vùng đang bật: VN TH SG MY ID PH KH LA CN TW HK JP KR IN AU US CA GB DE FR.
US và CA cùng `+1` nhưng có bộ quy tắc riêng. Khoá là mã vùng, không phải mã gọi.

## Menu và ánh xạ

Tạo các hàng từ dữ liệu, sau đó SHA-256 của nhãn hiển thị được dùng làm khoá
tra ID. Dùng hash tránh dấu chấm trong nhãn bị Get Dictionary Value hiểu thành
đường dẫn khoá lồng nhau. Các nhánh xử lý so sánh ID/handler cố định; không so
sánh chữ dịch, không tách số từ nhãn. Mỗi menu cần nhãn khác nhau trong cùng ngôn ngữ.

Handler hiện có: camera, photos, settings, about, cancel, manual, retry, country,
language, restore. Thêm một mục để gọi chức năng đã có chỉ sửa dữ liệu; thêm
chức năng chưa có cần bổ sung nhánh native và kiểm thử.

## Quy tắc sửa regex

1. Mã và số đều là văn bản. Dấu `+` và số `0` không được ép thành Number.
2. Kiểm tra NSN sau chuẩn hoá; dùng `\A` và `\z` để kiểm tra toàn bộ chuỗi.
3. Trong JSON, một dấu gạch chéo ngược phải được mã hoá thành `\\`.
4. Regex chạy theo ICU của iOS. Không giả định mọi tính năng PCRE/JavaScript đều dùng được.
5. Chỉ thêm vùng khi có dữ liệu nguồn, mẫu hợp lệ/không hợp lệ và kết quả đối chiếu.
6. Không tự mở rộng dải số, thêm chữ số thuê bao hoặc sửa O/I để ép một số thành hợp lệ.
7. Cập nhật `rulesRevision`/phiên bản catalog và giữ nguồn, giấy phép khi cập nhật metadata.

## Quy trình tạo bản thử nghiệm

```bash
python quick-call-image/src/catalog.py
python quick-call-image/src/build.py
python -m pip install -r quick-call-image/requirements-test.txt
python quick-call-image/tests/test_workflow.py
```

Sau khi các kiểm thử đạt, ký lại cả hai tệp trên Mac có quyền ký. Chạy bản Test
trên iPhone và đối chiếu từng chữ số với ảnh gốc trước khi thử bản chính.

## Đổi cấu hình trên thiết bị

Sửa tuỳ chọn qua menu là cách thông thường. Nếu thay `catalog.json` thủ công,
giữ bản sao và kiểm tra JSON trước khi chép vào QuickCall. JSON lỗi cú pháp có
thể khiến Get Dictionary from Input dừng ngay; lõi native không có try/catch
chung để bắt mọi lỗi. Xoá catalog hỏng để khởi tạo lại từ bản nhúng.

Thư mục trên thiết bị chỉ lưu cấu hình, không lưu ảnh, văn bản OCR hay nhật ký
cuộc gọi. Bản sao `settings.previous.json` chỉ được tạo khi đổi cài đặt.
