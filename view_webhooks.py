#!/usr/bin/env python3
"""
Script để xem và phân tích dữ liệu webhook đã lưu trong MongoDB
"""

import requests
import json
from datetime import datetime

def view_webhooks():
    """Xem danh sách webhooks"""
    print("📋 Danh sách webhooks đã nhận:")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:5000/webhooks?limit=10")
        if response.status_code == 200:
            data = response.json()
            webhooks = data.get('webhooks', [])
            
            if not webhooks:
                print("[ERROR] Chưa có webhook nào được nhận")
                return
            
            for i, webhook in enumerate(webhooks, 1):
                print(f"\n🔸 Webhook #{i}")
                print(f"   Thời gian: {webhook.get('timestamp', 'N/A')}")
                print(f"   Loại: {webhook.get('webhook_type', 'N/A')}")
                
                if webhook.get('webhook_type') == 'inbound_email':
                    email_data = webhook.get('email_data', {})
                    print(f"   Từ: {email_data.get('from', 'N/A')}")
                    print(f"   Đến: {email_data.get('to', 'N/A')}")
                    print(f"   Tiêu đề: {email_data.get('subject', 'N/A')}")
                    print(f"   Số file đính kèm: {email_data.get('attachment_count', '0')}")
                    
                    # Hiển thị nội dung email (rút gọn)
                    body_plain = email_data.get('body_plain', '')
                    if body_plain:
                        preview = body_plain[:100] + "..." if len(body_plain) > 100 else body_plain
                        print(f"   Nội dung: {preview}")
                
                elif webhook.get('webhook_type') == 'email_event':
                    print(f"   Event: {webhook.get('event_type', 'N/A')}")
                    print(f"   Message ID: {webhook.get('message_id', 'N/A')}")
                    print(f"   Recipient: {webhook.get('recipient', 'N/A')}")
                
                print("-" * 40)
        else:
            print(f"[ERROR] Lỗi: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"[ERROR] Lỗi kết nối: {e}")

def view_webhook_detail(webhook_id):
    """Xem chi tiết một webhook"""
    print(f"[SEARCH] Chi tiết webhook ID: {webhook_id}")
    print("=" * 60)
    
    try:
        response = requests.get(f"http://localhost:5000/webhook/{webhook_id}")
        if response.status_code == 200:
            data = response.json()
            webhook = data.get('webhook', {})
            
            print(f"Thời gian: {webhook.get('timestamp', 'N/A')}")
            print(f"Loại webhook: {webhook.get('webhook_type', 'N/A')}")
            print(f"IP: {webhook.get('ip_address', 'N/A')}")
            print(f"User Agent: {webhook.get('user_agent', 'N/A')}")
            
            if webhook.get('webhook_type') == 'inbound_email':
                email_data = webhook.get('email_data', {})
                print(f"\n📧 Thông tin Email:")
                print(f"   Từ: {email_data.get('from', 'N/A')}")
                print(f"   Đến: {email_data.get('to', 'N/A')}")
                print(f"   Tiêu đề: {email_data.get('subject', 'N/A')}")
                print(f"   Message ID: {email_data.get('message_id', 'N/A')}")
                print(f"   Timestamp: {email_data.get('timestamp', 'N/A')}")
                print(f"   Token: {email_data.get('token', 'N/A')}")
                print(f"   Signature: {email_data.get('signature', 'N/A')}")
                
                print(f"\n📄 Nội dung:")
                print(f"   Plain text: {email_data.get('body_plain', 'N/A')}")
                print(f"   HTML content: {email_data.get('body_html', 'N/A')}")
                print(f"   Stripped text: {email_data.get('stripped_text', 'N/A')}")
                print(f"   Stripped HTML: {email_data.get('stripped_html', 'N/A')}")
                print(f"   Stripped signature: {email_data.get('stripped_signature', 'N/A')}")
                
                # Hiển thị attachments
                attachments = email_data.get('attachments', [])
                if attachments:
                    print(f"\n📎 File đính kèm:")
                    for i, attachment in enumerate(attachments, 1):
                        print(f"   {i}. {attachment.get('name', 'N/A')}")
                        print(f"      Kích thước: {attachment.get('size', 'N/A')} bytes")
                        print(f"      Loại: {attachment.get('content_type', 'N/A')}")
            
            elif webhook.get('webhook_type') == 'email_event':
                print(f"\n📊 Thông tin Event:")
                print(f"   Event type: {webhook.get('event_type', 'N/A')}")
                print(f"   Message ID: {webhook.get('message_id', 'N/A')}")
                print(f"   Recipient: {webhook.get('recipient', 'N/A')}")
                print(f"   Domain: {webhook.get('domain', 'N/A')}")
            
            print(f"\n📋 Raw data:")
            print(json.dumps(webhook.get('form_data', {}), indent=2, ensure_ascii=False))
            
        elif response.status_code == 404:
            print("[ERROR] Không tìm thấy webhook với ID này")
        else:
            print(f"[ERROR] Lỗi: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"[ERROR] Lỗi kết nối: {e}")

def get_statistics():
    """Lấy thống kê webhooks"""
    print("[STATS] Thống kê webhooks:")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:5000/webhooks?limit=1000")
        if response.status_code == 200:
            data = response.json()
            webhooks = data.get('webhooks', [])
            
            if not webhooks:
                print("[ERROR] Chưa có webhook nào")
                return
            
            # Thống kê theo loại
            inbound_count = sum(1 for w in webhooks if w.get('webhook_type') == 'inbound_email')
            event_count = sum(1 for w in webhooks if w.get('webhook_type') == 'email_event')
            
            print(f"Tổng số webhooks: {len(webhooks)}")
            print(f"  - Inbound emails: {inbound_count}")
            print(f"  - Email events: {event_count}")
            
            # Thống kê events
            if event_count > 0:
                event_types = {}
                for w in webhooks:
                    if w.get('webhook_type') == 'email_event':
                        event_type = w.get('event_type', 'unknown')
                        event_types[event_type] = event_types.get(event_type, 0) + 1
                
                print(f"\n[CHART] Chi tiết events:")
                for event_type, count in event_types.items():
                    print(f"  - {event_type}: {count}")
            
            # Thống kê domains
            domains = {}
            for w in webhooks:
                if w.get('webhook_type') == 'inbound_email':
                    domain = w.get('email_data', {}).get('domain', 'unknown')
                    domains[domain] = domains.get(domain, 0) + 1
                elif w.get('webhook_type') == 'email_event':
                    domain = w.get('domain', 'unknown')
                    domains[domain] = domains.get(domain, 0) + 1
            
            if domains:
                print(f"\n[WEB] Domains:")
                for domain, count in domains.items():
                    print(f"  - {domain}: {count}")
            
        else:
            print(f"[ERROR] Lỗi: {response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] Lỗi kết nối: {e}")

def view_emails_by_recipient():
    """Xem emails theo người nhận"""
    print("[EMAIL] Xem emails theo người nhận:")
    print("=" * 60)
    
    recipient = input("Nhập email người nhận: ").strip()
    if not recipient:
        print("[ERROR] Vui lòng nhập email")
        return
    
    try:
        response = requests.get(f"http://localhost:5000/emails/search?to={recipient}&limit=10")
        if response.status_code == 200:
            data = response.json()
            emails = data.get('emails', [])
            
            if not emails:
                print(f"[ERROR] Không tìm thấy emails cho {recipient}")
                return
            
            print(f"\n[EMAIL] Tìm thấy {len(emails)} emails cho {recipient}:")
            for i, email in enumerate(emails, 1):
                email_data = email.get('email_data', {})
                print(f"\n[ITEM] Email #{i}")
                print(f"   ID: {email.get('_id', 'N/A')}")
                print(f"   Thời gian: {email.get('timestamp', 'N/A')}")
                print(f"   Từ: {email_data.get('from', 'N/A')}")
                print(f"   Tiêu đề: {email_data.get('subject', 'N/A')}")
                print(f"   Số file đính kèm: {email_data.get('attachment_count', '0')}")
                
                # Hiển thị nội dung email (rút gọn)
                body_plain = email_data.get('body_plain', '')
                body_html = email_data.get('body_html', '')
                if body_plain:
                    preview = body_plain[:100] + "..." if len(body_plain) > 100 else body_plain
                    print(f"   Nội dung (text): {preview}")
                if body_html:
                    # Loại bỏ HTML tags để hiển thị text
                    import re
                    html_text = re.sub('<[^<]+?>', '', body_html)
                    preview = html_text[:100] + "..." if len(html_text) > 100 else html_text
                    print(f"   Nội dung (HTML): {preview}")
                
                print("-" * 40)
        else:
            print(f"[ERROR] Lỗi: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"[ERROR] Lỗi kết nối: {e}")

def view_inbox(recipient):
    """Xem inbox của một người nhận"""
    print(f"[EMAIL] Inbox của {recipient}:")
    print("=" * 60)
    
    # Hỏi về subject filter
    subject_filter = input("Nhập subject filter (mặc định 'verification code'): ").strip()
    if not subject_filter:
        subject_filter = "verification code"
        print(f"[SEARCH] Sử dụng subject filter mặc định: '{subject_filter}'")
    else:
        print(f"[SEARCH] Sử dụng subject filter tùy chỉnh: '{subject_filter}'")
    
    try:
        url = f"http://localhost:5000/emails/inbox/{recipient}?limit=10&subject={subject_filter}"
        
        response = requests.get(url)
        if response.status_code == 200:
            html_content = response.text
            print(f"\n[EMAIL] Nhận được HTML content:")
            print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            print(f"   Length: {len(html_content)} ký tự")
            print(f"   Subject filter: '{subject_filter}'")
            
            # Hiển thị preview HTML content
            if html_content:
                # Loại bỏ HTML tags để hiển thị text preview
                import re
                html_text = re.sub('<[^<]+?>', '', html_content)
                preview = html_text[:200] + "..." if len(html_text) > 200 else html_text
                print(f"   Preview: {preview}")
                
                # Đếm số lượng email HTML (dựa trên số lượng div hoặc p tags)
                div_count = html_content.count('<div')
                p_count = html_content.count('<p')
                print(f"   Estimated emails: {max(div_count, p_count)}")
        elif response.status_code == 404:
            print(f"[ERROR] Không tìm thấy emails với HTML content cho {recipient} với subject filter '{subject_filter}'")
        else:
            print(f"[ERROR] Lỗi: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"[ERROR] Lỗi kết nối: {e}")

def main():
    """Menu chính"""
    while True:
        print("\n" + "=" * 60)
        print("🔧 Mailgun Webhook Viewer")
        print("=" * 60)
        print("1. Xem danh sách webhooks")
        print("2. Xem chi tiết webhook")
        print("3. Tìm kiếm emails theo người nhận")
        print("4. Xem inbox của một người nhận")
        print("5. Thống kê")
        print("6. Thoát")
        
        choice = input("\nChọn tùy chọn (1-6): ").strip()
        
        if choice == '1':
            view_webhooks()
        elif choice == '2':
            webhook_id = input("Nhập webhook ID: ").strip()
            if webhook_id:
                view_webhook_detail(webhook_id)
            else:
                print("[ERROR] Vui lòng nhập webhook ID")
        elif choice == '3':
            view_emails_by_recipient()
        elif choice == '4':
            recipient = input("Nhập email người nhận: ").strip()
            if recipient:
                view_inbox(recipient)
            else:
                print("[ERROR] Vui lòng nhập email")
        elif choice == '5':
            get_statistics()
        elif choice == '6':
            print("👋 Tạm biệt!")
            break
        else:
            print("[ERROR] Lựa chọn không hợp lệ")

if __name__ == "__main__":
    main() 