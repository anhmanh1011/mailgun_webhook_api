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
        logger.info(f"Form Data: {request.form.to_dict()}")
        logger.info(f"Raw Data Length: {len(request.get_data(as_text=True))}")
        
        # Tạo object request hoàn chỉnh để lưu vào database
        request_object = {
            'timestamp': datetime.now(),
            'request_metadata': {
                'url': request.url,
                'method': request.method,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'content_type': request.headers.get('Content-Type', ''),
                'content_length': request.headers.get('Content-Length', ''),
                'host': request.headers.get('Host', ''),
                'referer': request.headers.get('Referer', ''),
                'accept': request.headers.get('Accept', ''),
                'accept_encoding': request.headers.get('Accept-Encoding', ''),
                'accept_language': request.headers.get('Accept-Language', ''),
                'connection': request.headers.get('Connection', ''),
                'x_forwarded_for': request.headers.get('X-Forwarded-For', ''),
                'x_real_ip': request.headers.get('X-Real-IP', ''),
                'x_forwarded_proto': request.headers.get('X-Forwarded-Proto', ''),
            },
            'request_headers': dict(request.headers),
            'request_form_data': request.form.to_dict(),
            'request_raw_data': request.get_data(as_text=True),
            'request_json': None,
            'request_args': dict(request.args),
            'request_files': {},
            'webhook_type': 'unknown',
            'processed_data': {}
        }
        
        # Thử parse JSON nếu có
        try:
            if request.is_json:
                request_object['request_json'] = request.get_json()
        except Exception:
            pass
        
        
        
        # Xác định loại webhook và xử lý dữ liệu
        webhook_type = 'unknown'
        
        # # Kiểm tra nếu có event-data (webhook events)
        # if 'event-data' in request.form:
        #     try:
        #         import json
        #         event_data = json.loads(request.form['event-data'])
        #         webhook_type = 'email_event'
        #         request_object['webhook_type'] = webhook_type
        #         request_object['processed_data'] = {
        #             'event_type': event_data.get('event', 'unknown'),
        #             'message_id': event_data.get('message', {}).get('headers', {}).get('message-id', ''),
        #             'recipient': event_data.get('recipient', ''),
        #             'domain': event_data.get('domain', ''),
        #             'event_data': event_data
        #         }
        #         logger.info(f"Detected email event webhook: {event_data.get('event', 'unknown')}")
        #     except json.JSONDecodeError:
        #         logger.warning("Không thể parse event-data JSON")
        
        # # Xử lý dữ liệu inbound email (dựa trên Postbin data)
        # elif 'sender' in request.form:
        #     webhook_type = 'inbound_email'
        #     request_object['webhook_type'] = webhook_type
        #     request_object['processed_data'] = {
        #         'email_data': {
        #             'sender': request.form.get('sender', ''),
        #             'from': request.form.get('from', ''),
        #             'to': request.form.get('to', ''),
        #             'subject': request.form.get('subject', ''),
        #             'body_plain': request.form.get('body-plain', ''),
        #             'body_html': request.form.get('body-html', ''),
        #             'stripped_text': request.form.get('stripped-text', ''),
        #             'stripped_html': request.form.get('stripped-html', ''),
        #             'stripped_signature': request.form.get('stripped-signature', ''),
        #             'message_id': request.form.get('message-id', ''),
        #             'timestamp': request.form.get('timestamp', ''),
        #             'token': request.form.get('token', ''),
        #             'signature': request.form.get('signature', ''),
        #             'attachment_count': request.form.get('attachment-count', '0'),
        #             'recipient': request.form.get('recipient', ''),
        #             'domain': request.form.get('domain', ''),
        #             'message_headers': request.form.get('message-headers', ''),
        #             'content_id_map': request.form.get('content-id-map', ''),
        #             'attachments': []
        #         }
        #     }
        #     logger.info(f"Detected inbound email webhook from: {request.form.get('from', 'N/A')}")
        
        # Nếu không xác định được loại, lưu dữ liệu gốc
        # else:
        #     request_object['webhook_type'] = 'unknown'
        #     request_object['processed_data'] = {
        #         'raw_form_data': request.form.to_dict(),
        #         'raw_headers': dict(request.headers)
        #     }
        #     logger.info("Unknown webhook type, saving raw data")
        
        # Lưu vào MongoDB
        if mongodb_client is not None and webhooks_collection is not None:
            result = webhooks_collection.insert_one(request_object)
            logger.info(f"[SUCCESS] Webhook saved successfully with ID: {result.inserted_id}")
            logger.info(f"Webhook type: {webhook_type}")
            logger.info(f"Request object size: {len(str(request_object))} characters")
            
            response_data = {
                'status': 'success',
                'message': 'Webhook đã được xử lý và lưu thành công',
                'webhook_id': str(result.inserted_id),
                'webhook_type': webhook_type,
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
            'processed_data.email_data.to': {'$regex': to_email, '$options': 'i'}  # Case-insensitive search
        }
        
        # Lấy emails từ MongoDB
        emails = list(webhooks_collection.find(
            query,
            {
                '_id': 1,
                'timestamp': 1,
                'processed_data.email_data.from': 1,
                'processed_data.email_data.to': 1,
                'processed_data.email_data.subject': 1,
                'processed_data.email_data.body_plain': 1,
                'processed_data.email_data.body_html': 1,
                'processed_data.email_data.stripped_text': 1,
                'processed_data.email_data.stripped_html': 1,
                'processed_data.email_data.attachment_count': 1,
                'processed_data.email_data.message_id': 1
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
        subject_filter = request.args.get('subject', 'verification code').strip()
        
        # Tìm kiếm emails chính xác theo recipient
        query = {
            'webhook_type': 'inbound_email',
        }
        query['request_form_data.recipient'] = {'$regex': recipient, '$options': 'i'}

        # Thêm filter theo subject (mặc định là "verification code")
        query['request_form_data.subject'] = {'$regex': subject_filter, '$options': 'i'}
        logger.info(f"Using  filter: '{query}'")
        
        # Lấy emails từ MongoDB chỉ với body_html
        emails = list(webhooks_collection.find(
            query,
            {
                '_id': 1,
                'processed_data.email_data.body_html': 1
            }
        ).sort('timestamp', -1).skip(skip).limit(limit))
        
        # Chuẩn bị response HTML thuần túy
        html_contents = []
        for email in emails:
            email_data = email.get('processed_data', {}).get('email_data', {})
            body_html = email_data.get('body_html', '')
            if body_html:
                html_contents.append(body_html)
        
        # Trả về HTML thuần túy
        if html_contents:
            combined_html = "\n".join(html_contents)
            logger.info(f"[SUCCESS] Get inbox emails successful: {len(html_contents)} HTML emails found for '{recipient}' with subject='{subject_filter}'")
            logger.info(f"Combined HTML length: {len(combined_html)} characters")
            logger.info(f"Response Content-Type: text/html; charset=utf-8")
            return combined_html, 200, {'Content-Type': 'text/html; charset=utf-8'}
        else:
            logger.warning(f"[WARNING] No HTML emails found for recipient: {recipient} with subject='{subject_filter}'")
            logger.info(f"Response Content-Type: text/html; charset=utf-8")
            return "<p>not found</p>", 404, {'Content-Type': 'text/html; charset=utf-8'}
        
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
        
        email_data = email.get('processed_data', {}).get('email_data', {})
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