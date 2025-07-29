#!/usr/bin/env python3
"""
Script để test webhook endpoint
"""

import requests
import json
from datetime import datetime

# Cấu hình
WEBHOOK_URL = "http://localhost:5000/webhook/mailgun"
HEALTH_URL = "http://localhost:5000/health"

def test_health_check():
    """Test health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(HEALTH_URL)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

def test_mailgun_webhook():
    """Test webhook endpoint với dữ liệu thực tế từ Mailgun Postbin"""
    print("\n📧 Testing Mailgun webhook với dữ liệu thực tế...")
    
    # Dữ liệu thực tế từ Postbin http://bin.mailgun.net/71294e0#8ef1
    sample_webhook_data = {
        'sender': 'bob@baiburehconsortium.co.uk',
        'from': 'ross@baiburehconsortium.co.uk',
        'to': 'alice@example.com',
        'subject': 'Re: Hi Bob',
        'body-plain': 'Hi Alice,\n\nThis is Bob. I also attached a file.\n\nThanks,\nBob\n\nOn 04/26/2013 11:29 AM, Alice wrote:\n> Hi Bob,\n> \n> This is Alice. How are you doing?\n> \n> Thanks,\n> Alice',
        'body-html': '<div style="color: rgb(34, 34, 34); font-family: arial, sans-serif; font-size: 12.666666984558105px;">Hi Alice,</div><div><br></div><div>This is Bob.<span class="Apple-converted-space"> <img alt="" src="cid:part1.04060802.06030207@baiburehconsortium.co.uk" height="15" width="33"></span></div><div><br> I also attached a file.<br> <br></div><div>Thanks,</div><div>Bob</div><br> On 04/26/2013 11:29 AM, Alice wrote:<br>',
        'stripped-text': 'Hi Alice,\n\nThis is Bob. I also attached a file.\n\nThanks,\nBob',
        'stripped-signature': 'Thanks, Bob',
        'token': '48da0c42c4cb68e297f6bf29c36a19aa0a5dcadb42ab6eb0d2',
        'timestamp': '1753791508',
        'signature': '9509493e269f2e0c4a8536230f051ce2283f5335c2c91b12b5d7c5b8ea2adabb',
        'attachment-count': '1',
        'attachment-1': 'document.pdf',
        'attachment-1-size': '1024',
        'attachment-1-content-type': 'application/pdf',
        'message-id': '<test-message-id@baiburehconsortium.co.uk>',
        'recipient': 'alice@example.com',
        'domain': 'example.com'
    }
    
    try:
        response = requests.post(WEBHOOK_URL, data=sample_webhook_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

def test_email_event_webhook():
    """Test webhook endpoint với email events"""
    print("\n📧 Testing email event webhook...")
    
    # Dữ liệu mẫu cho email events
    sample_event_data = {
        'event-data': json.dumps({
            'event': 'delivered',
            'timestamp': 1234567890,
            'message': {
                'headers': {
                    'message-id': 'test-message-id-123',
                    'to': 'recipient@example.com',
                    'from': 'sender@example.com'
                }
            },
            'recipient': 'recipient@example.com',
            'domain': 'example.com',
            'ip': '192.168.1.1',
            'country': 'US',
            'region': 'CA',
            'city': 'San Francisco',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'device-type': 'desktop',
            'client-type': 'browser',
            'client-name': 'Chrome',
            'client-os': 'Windows',
            'mailing-list': None,
            'tag': ['tag1', 'tag2'],
            'campaigns': ['campaign1'],
            'user-variables': {
                'custom_var1': 'value1',
                'custom_var2': 'value2'
            }
        }),
        'signature': {
            'token': 'test-token',
            'timestamp': '1234567890',
            'signature': 'test-signature'
        }
    }
    
    try:
        response = requests.post(WEBHOOK_URL, data=sample_event_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

def test_get_webhooks():
    """Test endpoint lấy danh sách webhooks"""
    print("\n📋 Testing get webhooks...")
    try:
        response = requests.get("http://localhost:5000/webhooks?limit=5")
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Count: {result.get('count', 0)}")
        if result.get('webhooks'):
            print(f"First webhook timestamp: {result['webhooks'][0].get('timestamp', 'N/A')}")
            print(f"Webhook type: {result['webhooks'][0].get('webhook_type', 'N/A')}")
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

def test_search_emails():
    """Test endpoint tìm kiếm emails theo recipient"""
    print("\n🔍 Testing search emails...")
    try:
        # Test tìm kiếm với email từ test data
        response = requests.get("http://localhost:5000/emails/search?to=alice@example.com&limit=5")
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Query: {result.get('query', 'N/A')}")
        print(f"Count: {result.get('count', 0)}")
        if result.get('emails'):
            print(f"First email subject: {result['emails'][0].get('email_data', {}).get('subject', 'N/A')}")
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

def test_get_inbox():
    """Test endpoint lấy inbox emails"""
    print("\n📬 Testing get inbox...")
    try:
        # Test lấy inbox với email từ test data
        response = requests.get("http://localhost:5000/emails/inbox/alice@example.com?limit=5")
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            html_content = response.text
            print(f"HTML content length: {len(html_content)}")
            print(f"HTML preview: {html_content[:200]}...")
            
            # Kiểm tra xem có HTML tags không
            if '<' in html_content and '>' in html_content:
                print("[SUCCESS] Response contains HTML content")
            else:
                print("[ERROR] Response does not contain HTML content")
        elif response.status_code == 404:
            print("404: No HTML emails found")
        else:
            print(f"Unexpected status code: {response.status_code}")
        
        # Test với subject filter mặc định
        print("\n🔍 Testing with default subject filter...")
        response_with_default_filter = requests.get("http://localhost:5000/emails/inbox/alice@example.com?limit=5")
        print(f"Status Code (default filter): {response_with_default_filter.status_code}")
        print(f"Content-Type (default filter): {response_with_default_filter.headers.get('Content-Type', 'N/A')}")
        
        if response_with_default_filter.status_code == 200:
            html_content_default = response_with_default_filter.text
            print(f"Default filter HTML content length: {len(html_content_default)}")
        elif response_with_default_filter.status_code == 404:
            print("404: No HTML emails found with default subject filter")
        
        # Test với subject filter tùy chỉnh
        print("\n🔍 Testing with custom subject filter...")
        response_with_custom_filter = requests.get("http://localhost:5000/emails/inbox/alice@example.com?subject=password&limit=5")
        print(f"Status Code (custom filter): {response_with_custom_filter.status_code}")
        print(f"Content-Type (custom filter): {response_with_custom_filter.headers.get('Content-Type', 'N/A')}")
        
        if response_with_custom_filter.status_code == 200:
            html_content_custom = response_with_custom_filter.text
            print(f"Custom filter HTML content length: {len(html_content_custom)}")
        elif response_with_custom_filter.status_code == 404:
            print("404: No HTML emails found with custom subject filter")
            
        return response.status_code in [200, 404]
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

def main():
    """Chạy tất cả tests"""
    print("🚀 Starting API tests...")
    print("=" * 50)
    
    # Test health check
    health_ok = test_health_check()
    
    if health_ok:
        print("[SUCCESS] Health check passed")
        
        # Test inbound email webhook
        inbound_webhook_ok = test_mailgun_webhook()
        if inbound_webhook_ok:
            print("[SUCCESS] Inbound email webhook test passed")
            
            # Test email event webhook
            event_webhook_ok = test_email_event_webhook()
            if event_webhook_ok:
                print("[SUCCESS] Email event webhook test passed")
                
                # Test get webhooks
                get_webhooks_ok = test_get_webhooks()
                if get_webhooks_ok:
                    print("[SUCCESS] Get webhooks test passed")
                    
                    # Test search emails
                    search_emails_ok = test_search_emails()
                    if search_emails_ok:
                        print("[SUCCESS] Search emails test passed")
                        
                        # Test get inbox
                        get_inbox_ok = test_get_inbox()
                        if get_inbox_ok:
                            print("[SUCCESS] Get inbox test passed")
                        else:
                            print("[ERROR] Get inbox test failed")
                    else:
                        print("[ERROR] Search emails test failed")
                else:
                    print("[ERROR] Get webhooks test failed")
            else:
                print("[ERROR] Email event webhook test failed")
        else:
            print("[ERROR] Inbound email webhook test failed")
    else:
        print("[ERROR] Health check failed")
        print("[WARNING] Make sure the API is running on http://localhost:5000")
    
    print("\n" + "=" * 50)
    print("🏁 Tests completed!")

if __name__ == "__main__":
    main() 