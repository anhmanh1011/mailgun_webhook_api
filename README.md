# Mailgun Webhook API

API Python để nhận webhook từ Mailgun và lưu vào MongoDB.

## Tính năng

- Nhận webhook từ Mailgun
- Lưu dữ liệu webhook vào MongoDB
- API để xem danh sách webhooks đã nhận
- API để xem chi tiết webhook theo ID
- Health check endpoint

## Cài đặt

1. Clone repository này
2. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

3. Tạo file `.env` từ `env_example.txt`:
```bash
cp env_example.txt .env
```

4. Cập nhật thông tin trong file `.env`:
```
DB_USERNAME=your_mongodb_username
DB_PASSWORD=your_mongodb_password
```

## Chạy ứng dụng

### Development
```bash
python app.py
```

### Production (với Gunicorn)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## API Endpoints

### 1. Health Check
```
GET /health
```
Kiểm tra trạng thái của API và kết nối MongoDB.

### 2. Webhook Mailgun
```
POST /webhook/mailgun
```
Endpoint để nhận webhook từ Mailgun.

### 3. Lấy danh sách webhooks
```
GET /webhooks?limit=50&skip=0
```
- `limit`: Số lượng webhooks trả về (mặc định: 50)
- `skip`: Số webhooks bỏ qua (mặc định: 0)

### 4. Lấy chi tiết webhook
```
GET /webhook/<webhook_id>
```

### 5. Tìm kiếm emails theo người nhận
```
GET /emails/search?to=email@example.com&limit=50&skip=0
```
- `to`: Email người nhận (bắt buộc)
- `limit`: Số lượng emails trả về (mặc định: 50)
- `skip`: Số emails bỏ qua (mặc định: 0)

### 6. Lấy chi tiết email
```
GET /emails/<email_id>
```

### 7. Lấy inbox emails của một người nhận
```
GET /emails/inbox/<recipient>?limit=50&skip=0&subject=verification%20code
```
- `recipient`: Email người nhận (trong URL path)
- `limit`: Số lượng emails trả về (mặc định: 50)
- `skip`: Số emails bỏ qua (mặc định: 0)
- `subject`: Lọc theo subject chứa từ khóa (mặc định: "verification code")
- **Trả về**: Nội dung HTML thuần túy (Content-Type: text/html)

### 8. Lấy nội dung HTML của email
```
GET /emails/<email_id>/html
```
- `email_id`: ID của email
- Trả về nội dung HTML đầy đủ của email

## Cấu hình Mailgun

### 1. Inbound Email Webhook
1. Đăng nhập vào Mailgun Dashboard
2. Vào phần "Receiving" > "Routes"
3. Tạo route mới hoặc chỉnh sửa route hiện có
4. Thêm webhook URL: `https://your-domain.com/webhook/mailgun`
5. Chọn action "Store and notify" hoặc "Forward"

### 2. Email Event Webhook
1. Đăng nhập vào Mailgun Dashboard
2. Vào phần "Webhooks"
3. Thêm webhook URL: `https://your-domain.com/webhook/mailgun`
4. Chọn các events bạn muốn nhận (delivered, opened, clicked, etc.)

## Cấu trúc dữ liệu

API hỗ trợ 2 loại webhook từ Mailgun:

### 1. Inbound Email Webhook
Khi có email được gửi đến domain của bạn:

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "webhook_type": "inbound_email",
  "headers": {...},
  "form_data": {...},
  "raw_data": "...",
  "ip_address": "192.168.1.1",
  "user_agent": "...",
  "email_data": {
    "sender": "sender@example.com",
    "from": "sender@example.com",
    "to": "recipient@example.com",
    "subject": "Email Subject",
    "body_plain": "Plain text content",
    "body_html": "<html>HTML content</html>",
    "stripped_text": "Text without signature",
    "stripped_html": "<html>HTML content without signature</html>",
    "stripped_signature": "Signature only",
    "message_id": "<message-id@domain.com>",
    "timestamp": "1753791508",
    "token": "webhook_token",
    "signature": "webhook_signature",
    "attachment_count": "1",
    "attachments": [
      {
        "name": "document.pdf",
        "size": "1024",
        "content_type": "application/pdf"
      }
    ]
  }
}
```

### 2. Email Event Webhook
Khi có sự kiện xảy ra với email (delivered, opened, clicked, etc.):

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "webhook_type": "email_event",
  "headers": {...},
  "form_data": {...},
  "raw_data": "...",
  "ip_address": "192.168.1.1",
  "user_agent": "...",
  "event_type": "delivered",
  "message_id": "...",
  "recipient": "user@example.com",
  "domain": "example.com"
}
```

## Logging

API có hệ thống logging chi tiết để theo dõi:

### Log Files
- **`app.log`**: File log chính chứa tất cả request/response
- **Console**: Logs cũng được hiển thị trên console

### Logging Features
- **Request Logging**: URL, method, headers, IP, user agent
- **Response Logging**: Status code, content type, response data
- **Error Logging**: Chi tiết lỗi với stack trace
- **Success Logging**: Thông báo thành công với dữ liệu

### View Logs
```bash
# Xem logs bằng script
python view_logs.py

# Xem logs trực tiếp
tail -f app.log
```

## Bảo mật

- Sử dụng environment variables cho thông tin nhạy cảm
- Có thể thêm authentication cho các endpoints nếu cần
- Validate dữ liệu webhook từ Mailgun

## Troubleshooting

### Lỗi kết nối MongoDB
- Kiểm tra username/password trong file `.env`
- Đảm bảo IP của server được whitelist trong MongoDB Atlas
- Kiểm tra connection string

### Webhook không được nhận
- Kiểm tra URL webhook trong Mailgun
- Đảm bảo server có thể truy cập từ internet
- Kiểm tra logs của ứng dụng

## License

MIT

## Subject Filter Examples

### Tìm kiếm emails với subject filter:

```bash
# Sử dụng subject filter mặc định "verification code"
curl "http://localhost:5000/emails/inbox/alice@example.com"

# Tìm emails có subject chứa "verification code" (tương tự mặc định)
curl "http://localhost:5000/emails/inbox/alice@example.com?subject=verification%20code"

# Tìm emails có subject chứa "password"
curl "http://localhost:5000/emails/inbox/alice@example.com?subject=password"

# Tìm emails có subject chứa "reset"
curl "http://localhost:5000/emails/inbox/alice@example.com?subject=reset"
```

**Tính năng Subject Filter:**
- **Mặc định**: "verification code" nếu không có tham số subject
- Tìm kiếm không phân biệt hoa thường (case-insensitive)
- Hỗ trợ tìm kiếm từ khóa một phần
- Kết hợp với recipient filter
- Logging chi tiết về subject filter được sử dụng 