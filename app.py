from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Request/Response logging middleware
@app.before_request
def log_request():
    """Log incoming request"""
    logger.info(f"REQUEST: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Remote IP: {request.remote_addr}")
    logger.info(f"User Agent: {request.headers.get('User-Agent', 'N/A')}")
    
    # Log request data for POST requests
    if request.method == 'POST':
        logger.info(f"Form Data: {request.form.to_dict()}")
        logger.info(f"Raw Data: {request.get_data(as_text=True)[:500]}...")  # Limit to 500 chars

@app.after_request
def log_response(response):
    """Log outgoing response"""
    logger.info(f"RESPONSE: {response.status_code} {response.status}")
    logger.info(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
    logger.info(f"Content-Length: {response.headers.get('Content-Length', 'N/A')}")
    
    # Log response content for small responses
    if response.content_length and response.content_length < 1000:
        logger.info(f"Response Content: {response.get_data(as_text=True)[:500]}...")
    
    return response

# MongoDB connection
def get_mongodb_client():
    """Tạo kết nối MongoDB"""
    try:
        # Lấy thông tin đăng nhập từ environment variables
        db_username = os.getenv('DB_USERNAME', 'your_username')
        db_password = os.getenv('DB_PASSWORD', 'your_password')
        
        # Connection string
        connection_string = f"mongodb+srv://{db_username}:{db_password}@daomanh.7rbkw2e.mongodb.net/?retryWrites=true&w=majority&appName=daomanh"
        
        client = MongoClient(connection_string)
        # Test connection
        client.admin.command('ping')
        logger.info("Kết nối MongoDB thành công!")
        return client
    except Exception as e:
        logger.error(f"Lỗi kết nối MongoDB: {e}")
        return None

# Initialize MongoDB client
mongodb_client = get_mongodb_client()
if mongodb_client:
    db = mongodb_client['mailgun_webhooks']
    webhooks_collection = db['webhooks']

@app.route('/health', methods=['GET'])
def health_check():
    """Kiểm tra sức khỏe của API"""
    logger.info("=== HEALTH CHECK REQUEST ===")
    try:
        if mongodb_client:
            mongodb_client.admin.command('ping')
            response_data = {
                'status': 'healthy',
                'mongodb': 'connected',
                'timestamp': datetime.now().isoformat()
            }
            logger.info(f"Health check successful: {response_data}")
            return jsonify(response_data), 200
        else:
            response_data = {
                'status': 'unhealthy',
                'mongodb': 'disconnected',
                'timestamp': datetime.now().isoformat()
            }
            logger.warning(f"Health check failed - MongoDB disconnected: {response_data}")
            return jsonify(response_data), 503
    except Exception as e:
        response_data = {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        logger.error(f"Health check error: {response_data}")
        return jsonify(response_data), 503

@app.route('/webhook/mailgun', methods=['POST'])
def mailgun_webhook():
    """Nhận webhook từ Mailgun"""
    logger.info("=== MAILGUN WEBHOOK REQUEST ===")
    logger.info(f"Request URL: {request.url}")
    logger.info(f"Request Method: {request.method}")
    logger.info(f"Remote IP: {request.remote_addr}")
    logger.info(f"User Agent: {request.headers.get('User-Agent', 'N/A')}")
    logger.info(f"Content-Type: {request.headers.get('Content-Type', 'N/A')}")
    
    try:
        # Log request data
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Form Data: {request.get_data(as_text=True)}")
        logger.info(f"Raw Data Length: {len(request.get_data(as_text=True))}")
        
        # Lấy dữ liệu từ webhook
        webhook_data = {
            'timestamp': datetime.now(),
            'headers': dict(request.headers),
            'email_data': request.get_json(),
            'raw_data': request.get_data(as_text=True),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
        }
        
        # Xác định loại webhook và xử lý dữ liệu
        webhook_data['webhook_type'] = 'inbound_email'  # Mặc định là inbound email
        
        
        # Xử lý dữ liệu inbound email (dựa trên Postbin data)
        # if 'sender' in request.form:
        # webhook_data['email_data'] = {
        #     'sender': request.form.get('sender', ''),
        #     'from': request.form.get('from', ''),
        #     'to': request.form.get('to', ''),
        #     'subject': request.form.get('subject', ''),
        #     'body_plain': request.form.get('body-plain', ''),
        #     'body_html': request.form.get('body-html', ''),
        #     'stripped_text': request.form.get('stripped-text', ''),
        #     'stripped_html': request.form.get('stripped-html', ''),
        #     'stripped_signature': request.form.get('stripped-signature', ''),
        #     'message_id': request.form.get('message-id', ''),
        #     'timestamp': request.form.get('timestamp', ''),
        #     'token': request.form.get('token', ''),
        #     'signature': request.form.get('signature', ''),
        #     'attachment_count': request.form.get('attachment-count', '0'),
        #     'recipient': request.form.get('recipient', ''),
        #     'domain': request.form.get('domain', ''),
        #     'message_headers': request.form.get('message-headers', ''),
        #     'content_id_map': request.form.get('content-id-map', ''),
        #     'attachments': []
        # }
            
            # # Xử lý attachments nếu có
            # attachment_count = int(request.form.get('attachment-count', 0))
            # for i in range(attachment_count):
            #     attachment_data = {
            #         'name': request.form.get(f'attachment-{i+1}', ''),
            #         'size': request.form.get(f'attachment-{i+1}-size', ''),
            #         'content_type': request.form.get(f'attachment-{i+1}-content-type', ''),
            #         'url': request.form.get(f'attachment-{i+1}-url', '')
            #     }
            #     webhook_data['email_data']['attachments'].append(attachment_data)
        
        # Lưu vào MongoDB
        if mongodb_client is not None and webhooks_collection is not None:
            result = webhooks_collection.insert_one(webhook_data)
            logger.info(f"[SUCCESS] Webhook saved successfully with ID: {result.inserted_id}")
            
            response_data = {
                'status': 'success',
                'message': 'Webhook đã được xử lý và lưu thành công',
                'webhook_id': str(result.inserted_id),
                'timestamp': datetime.now().isoformat()
            }
            logger.info(f"Webhook response: {response_data}")
            return jsonify(response_data), 200
        else:
            logger.error("[ERROR] Cannot connect to MongoDB")
            response_data = {
                'status': 'error',
                'message': 'Lỗi kết nối database'
            }
            logger.error(f"Webhook error response: {response_data}")
            return jsonify(response_data), 500
            
    except Exception as e:
        logger.error(f"[ERROR] Webhook processing error: {e}")
        response_data = {
            'status': 'error',
            'message': f'Lỗi xử lý webhook: {str(e)}'
        }
        logger.error(f"Webhook exception response: {response_data}")
        return jsonify(response_data), 500

@app.route('/webhooks', methods=['GET'])
def get_webhooks():
    """Lấy danh sách webhooks đã nhận"""
    logger.info("=== GET WEBHOOKS REQUEST ===")
    logger.info(f"Request URL: {request.url}")
    logger.info(f"Query Parameters: {dict(request.args)}")
    
    try:
        if mongodb_client is None or webhooks_collection is None:
            logger.error("[ERROR] Cannot connect to MongoDB")
            response_data = {
                'status': 'error',
                'message': 'Không thể kết nối database'
            }
            logger.error(f"Get webhooks error response: {response_data}")
            return jsonify(response_data), 500
        
        # Lấy tham số query
        limit = int(request.args.get('limit', 50))
        skip = int(request.args.get('skip', 0))
        
        # Lấy webhooks từ MongoDB
        webhooks = list(webhooks_collection.find(
            {},
            {'_id': 0}  # Loại bỏ _id field
        ).sort('timestamp', -1).skip(skip).limit(limit))
        
        # Convert datetime objects to string
        for webhook in webhooks:
            if 'timestamp' in webhook:
                webhook['timestamp'] = webhook['timestamp'].isoformat()
        
        response_data = {
            'status': 'success',
            'count': len(webhooks),
            'webhooks': webhooks
        }
        logger.info(f"[SUCCESS] Get webhooks successful: {len(webhooks)} webhooks found")
        logger.info(f"Get webhooks response: {response_data}")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"[ERROR] Get webhooks error: {e}")
        response_data = {
            'status': 'error',
            'message': f'Lỗi lấy webhooks: {str(e)}'
        }
        logger.error(f"Get webhooks exception response: {response_data}")
        return jsonify(response_data), 500

@app.route('/webhook/<webhook_id>', methods=['GET'])
def get_webhook_by_id(webhook_id):
    """Lấy thông tin chi tiết của một webhook"""
    logger.info("=== GET WEBHOOK BY ID REQUEST ===")
    logger.info(f"Request URL: {request.url}")
    logger.info(f"Webhook ID: {webhook_id}")
    
    try:
        if mongodb_client is None or webhooks_collection is None:
            logger.error("[ERROR] Cannot connect to MongoDB")
            response_data = {
                'status': 'error',
                'message': 'Không thể kết nối database'
            }
            logger.error(f"Get webhook by ID error response: {response_data}")
            return jsonify(response_data), 500
        
        from bson import ObjectId
        webhook = webhooks_collection.find_one({'_id': ObjectId(webhook_id)})
        
        if not webhook:
            logger.warning(f"[WARNING] Webhook not found: {webhook_id}")
            response_data = {
                'status': 'error',
                'message': 'Không tìm thấy webhook'
            }
            logger.warning(f"Get webhook by ID not found response: {response_data}")
            return jsonify(response_data), 404
        
        # Convert ObjectId to string
        webhook['_id'] = str(webhook['_id'])
        if 'timestamp' in webhook:
            webhook['timestamp'] = webhook['timestamp'].isoformat()
        
        response_data = {
            'status': 'success',
            'webhook': webhook
        }
        logger.info(f"[SUCCESS] Get webhook by ID successful: {webhook_id}")
        logger.info(f"Get webhook by ID response: {response_data}")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"[ERROR] Get webhook by ID error: {e}")
        response_data = {
            'status': 'error',
            'message': f'Lỗi lấy webhook: {str(e)}'
        }
        logger.error(f"Get webhook by ID exception response: {response_data}")
        return jsonify(response_data), 500

@app.route('/emails/search', methods=['GET'])
def search_emails_by_recipient():
    """Tìm kiếm emails theo người nhận (to)"""
    logger.info("=== SEARCH EMAILS REQUEST ===")
    logger.info(f"Request URL: {request.url}")
    logger.info(f"Query Parameters: {dict(request.args)}")
    
    try:
        if mongodb_client is None or webhooks_collection is None:
            logger.error("[ERROR] Cannot connect to MongoDB")
            response_data = {
                'status': 'error',
                'message': 'Không thể kết nối database'
            }
            logger.error(f"Search emails error response: {response_data}")
            return jsonify(response_data), 500
        
        # Lấy tham số query
        to_email = request.args.get('to', '').strip()
        limit = int(request.args.get('limit', 50))
        skip = int(request.args.get('skip', 0))
        
        if not to_email:
            return jsonify({
                'status': 'error',
                'message': 'Tham số "to" là bắt buộc'
            }), 400
        
        # Tìm kiếm webhooks có email_data.to khớp với to_email
        query = {
            'webhook_type': 'inbound_email',
            'email_data.to': {'$regex': to_email, '$options': 'i'}  # Case-insensitive search
        }
        
        # Lấy emails từ MongoDB
        emails = list(webhooks_collection.find(
            query,
            {
                '_id': 1,
                'timestamp': 1,
                'email_data.from': 1,
                'email_data.to': 1,
                'email_data.subject': 1,
                'email_data.body_plain': 1,
                'email_data.body_html': 1,
                'email_data.stripped_text': 1,
                'email_data.stripped_html': 1,
                'email_data.attachment_count': 1,
                'email_data.message_id': 1
            }
        ).sort('timestamp', -1).skip(skip).limit(limit))
        
        # Convert datetime objects to string
        for email in emails:
            email['_id'] = str(email['_id'])
            if 'timestamp' in email:
                email['timestamp'] = email['timestamp'].isoformat()
        
        response_data = {
            'status': 'success',
            'query': f'to: {to_email}',
            'count': len(emails),
            'emails': emails
        }
        logger.info(f"[SUCCESS] Search emails successful: {len(emails)} emails found for '{to_email}'")
        logger.info(f"Search emails response: {response_data}")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"[ERROR] Search emails error: {e}")
        response_data = {
            'status': 'error',
            'message': f'Lỗi tìm kiếm emails: {str(e)}'
        }
        logger.error(f"Search emails exception response: {response_data}")
        return jsonify(response_data), 500

@app.route('/emails/<email_id>', methods=['GET'])
def get_email_by_id(email_id):
    """Lấy thông tin chi tiết của một email"""
    try:
        if mongodb_client is None or webhooks_collection is None:
            return jsonify({
                'status': 'error',
                'message': 'Không thể kết nối database'
            }), 500
        
        from bson import ObjectId
        email = webhooks_collection.find_one({
            '_id': ObjectId(email_id),
            'webhook_type': 'inbound_email'
        })
        
        if not email:
            return jsonify({
                'status': 'error',
                'message': 'Không tìm thấy email'
            }), 404
        
        # Convert ObjectId to string
        email['_id'] = str(email['_id'])
        if 'timestamp' in email:
            email['timestamp'] = email['timestamp'].isoformat()
        
        return jsonify({
            'status': 'success',
            'email': email
        }), 200
        
    except Exception as e:
        logger.error(f"Lỗi lấy email: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Lỗi lấy email: {str(e)}'
        }), 500

@app.route('/emails/inbox/<recipient>', methods=['GET'])
def get_inbox_emails(recipient):
    """Lấy tất cả emails trong inbox của một người nhận"""
    logger.info("=== GET INBOX EMAILS REQUEST ===")
    logger.info(f"Request URL: {request.url}")
    logger.info(f"Recipient: {recipient}")
    logger.info(f"Query Parameters: {dict(request.args)}")
    
    try:
        if mongodb_client is None or webhooks_collection is None:
            logger.error("[ERROR] Cannot connect to MongoDB")
            response_data = {
                'status': 'error',
                'message': 'Không thể kết nối database'
            }
            logger.error(f"Get inbox emails error response: {response_data}")
            return jsonify(response_data), 500
        
        # Lấy tham số query
        limit = int(request.args.get('limit', 50))
        skip = int(request.args.get('skip', 0))
        # Tìm kiếm emails chính xác theo recipient
        query = {
            'webhook_type': 'inbound_email',
            'email_data.to': recipient,
            "email_data.subject": {
                "$regex": "verification code",  # tự động tìm chứa chuỗi
                "$options": "i"  # không phân biệt chữ hoa chữ thường
            }
        }
        
        # Thêm filter theo subject (mặc định là "verification code")
        
        # Lấy emails từ MongoDB chỉ với body_html
        emails = list(webhooks_collection.find(
            query,
            {
                '_id': 1,
                'email_data.body_html': 1
            }
        ).sort('timestamp', -1).skip(skip).limit(limit))
        
        # Chuẩn bị response HTML thuần túy
        html_contents = []
        for email in emails:
            body_html = email.get('email_data', {}).get('body_html', '')
            if body_html:
                html_contents.append(body_html)
        
        # Trả về HTML thuần túy
        if html_contents:
            combined_html = "\n".join(html_contents)
            logger.info(f"Combined HTML length: {len(combined_html)} characters")
            logger.info(f"Response Content-Type: text/html; charset=utf-8")
            return combined_html, 200, {'Content-Type': 'text/html; charset=utf-8'}
        else:
            logger.info(f"Response Content-Type: text/html; charset=utf-8")
            return "<p>not found</p>  ", 404, {'Content-Type': 'text/html; charset=utf-8'}
        
    except Exception as e:
        logger.error(f"[ERROR] Get inbox emails error: {e}")
        response_data = {
            'status': 'error',
            'message': f'Lỗi lấy inbox emails: {str(e)}'
        }
        logger.error(f"Get inbox emails exception response: {response_data}")
        return jsonify(response_data), 500

@app.route('/emails/<email_id>/html', methods=['GET'])
def get_email_html_content(email_id):
    """Lấy nội dung HTML của một email"""
    try:
        if mongodb_client is None or webhooks_collection is None:
            return jsonify({
                'status': 'error',
                'message': 'Không thể kết nối database'
            }), 500
        
        from bson import ObjectId
        email = webhooks_collection.find_one({
            '_id': ObjectId(email_id),
            'webhook_type': 'inbound_email'
        })
        
        if not email:
            return jsonify({
                'status': 'error',
                'message': 'Không tìm thấy email'
            }), 404
        
        email_data = email.get('email_data', {})
        html_content = email_data.get('body_html', '')
        stripped_html = email_data.get('stripped_html', '')
        
        return jsonify({
            'status': 'success',
            'email_id': str(email['_id']),
            'subject': email_data.get('subject', ''),
            'from': email_data.get('from', ''),
            'to': email_data.get('to', ''),
            'html_content': html_content,
            'stripped_html': stripped_html,
            'has_html': bool(html_content or stripped_html)
        }), 200
        
    except Exception as e:
        logger.error(f"Lỗi lấy HTML content: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Lỗi lấy HTML content: {str(e)}'
        }), 500

@app.errorhandler(404)
def not_found(error):
    logger.error(f"[ERROR] 404 Error: {request.url} - Endpoint không tồn tại")
    response_data = {
        'status': 'error',
        'message': 'Endpoint không tồn tại'
    }
    logger.error(f"404 Error response: {response_data}")
    return jsonify(response_data), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"[ERROR] 500 Error: {request.url} - Lỗi server nội bộ")
    response_data = {
        'status': 'error',
        'message': 'Lỗi server nội bộ'
    }
    logger.error(f"500 Error response: {response_data}")
    return jsonify(response_data), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 