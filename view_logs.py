#!/usr/bin/env python3
"""
Script để xem và phân tích logs của API
"""

import os
import re
from datetime import datetime, timedelta

def view_recent_logs(lines=50):
    """Xem logs gần đây"""
    print("📋 Logs gần đây:")
    print("=" * 80)
    
    if not os.path.exists('app.log'):
        print("❌ File app.log không tồn tại")
        return
    
    try:
        with open('app.log', 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            
        # Lấy dòng cuối cùng
        recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        for line in recent_lines:
            print(line.strip())
            
    except Exception as e:
        print(f"❌ Lỗi đọc file log: {e}")

def view_requests_by_type():
    """Xem thống kê requests theo loại"""
    print("📊 Thống kê requests theo loại:")
    print("=" * 80)
    
    if not os.path.exists('app.log'):
        print("❌ File app.log không tồn tại")
        return
    
    try:
        with open('app.log', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Tìm các loại request
        request_types = {
            'HEALTH CHECK': len(re.findall(r'=== HEALTH CHECK REQUEST ===', content)),
            'MAILGUN WEBHOOK': len(re.findall(r'=== MAILGUN WEBHOOK REQUEST ===', content)),
            'GET WEBHOOKS': len(re.findall(r'=== GET WEBHOOKS REQUEST ===', content)),
            'GET WEBHOOK BY ID': len(re.findall(r'=== GET WEBHOOK BY ID REQUEST ===', content)),
            'SEARCH EMAILS': len(re.findall(r'=== SEARCH EMAILS REQUEST ===', content)),
            'GET INBOX EMAILS': len(re.findall(r'=== GET INBOX EMAILS REQUEST ===', content)),
        }
        
        total_requests = sum(request_types.values())
        print(f"Tổng số requests: {total_requests}")
        print()
        
        for request_type, count in request_types.items():
            if count > 0:
                percentage = (count / total_requests * 100) if total_requests > 0 else 0
                print(f"  {request_type}: {count} ({percentage:.1f}%)")
                
    except Exception as e:
        print(f"❌ Lỗi phân tích logs: {e}")

def view_errors():
    """Xem các lỗi trong logs"""
    print("❌ Các lỗi trong logs:")
    print("=" * 80)
    
    if not os.path.exists('app.log'):
        print("❌ File app.log không tồn tại")
        return
    
    try:
        with open('app.log', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        error_lines = []
        for line in lines:
            if 'ERROR' in line or '❌' in line:
                error_lines.append(line.strip())
        
        if error_lines:
            print(f"Tìm thấy {len(error_lines)} lỗi:")
            print()
            for i, error in enumerate(error_lines[-20:], 1):  # Hiển thị 20 lỗi gần nhất
                print(f"{i}. {error}")
        else:
            print("[SUCCESS] Không có lỗi nào được tìm thấy")
            
    except Exception as e:
        print(f"❌ Lỗi đọc logs: {e}")

def view_successful_operations():
    """Xem các thao tác thành công"""
    print("[SUCCESS] Các thao tác thành công:")
    print("=" * 80)
    
    if not os.path.exists('app.log'):
        print("❌ File app.log không tồn tại")
        return
    
    try:
        with open('app.log', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Tìm các thao tác thành công
        success_patterns = [
            r'[SUCCESS] Webhook saved successfully with ID: ([^\n]+)',
            r'[SUCCESS] Get webhooks successful: (\d+) webhooks found',
            r'[SUCCESS] Get webhook by ID successful: ([^\n]+)',
            r'[SUCCESS] Search emails successful: (\d+) emails found for \'([^\']+)\'',
            r'[SUCCESS] Get inbox emails successful: (\d+) HTML emails found for \'([^\']+)\'',
        ]
        
        for pattern in success_patterns:
            matches = re.findall(pattern, content)
            if matches:
                print(f"Pattern: {pattern}")
                for match in matches[-5:]:  # Hiển thị 5 kết quả gần nhất
                    print(f"  - {match}")
                print()
                
    except Exception as e:
        print(f"❌ Lỗi phân tích logs: {e}")

def view_webhook_details():
    """Xem chi tiết webhook requests"""
    print("📧 Chi tiết webhook requests:")
    print("=" * 80)
    
    if not os.path.exists('app.log'):
        print("❌ File app.log không tồn tại")
        return
    
    try:
        with open('app.log', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        webhook_sections = []
        current_section = []
        in_webhook = False
        
        for line in lines:
            if '=== MAILGUN WEBHOOK REQUEST ===' in line:
                if current_section:
                    webhook_sections.append(current_section)
                current_section = [line.strip()]
                in_webhook = True
            elif in_webhook:
                current_section.append(line.strip())
                if 'Webhook response:' in line or 'Webhook error response:' in line:
                    in_webhook = False
        
        if current_section:
            webhook_sections.append(current_section)
        
        print(f"Tìm thấy {len(webhook_sections)} webhook requests:")
        print()
        
        for i, section in enumerate(webhook_sections[-3:], 1):  # Hiển thị 3 webhook gần nhất
            print(f"Webhook #{i}:")
            for line in section:
                print(f"  {line}")
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ Lỗi phân tích webhook logs: {e}")

def main():
    """Menu chính"""
    while True:
        print("\n" + "=" * 80)
        print("🔧 Log Viewer")
        print("=" * 80)
        print("1. Xem logs gần đây")
        print("2. Thống kê requests theo loại")
        print("3. Xem các lỗi")
        print("4. Xem thao tác thành công")
        print("5. Xem chi tiết webhook")
        print("6. Thoát")
        
        choice = input("\nChọn tùy chọn (1-6): ").strip()
        
        if choice == '1':
            lines = input("Số dòng muốn xem (mặc định 50): ").strip()
            lines = int(lines) if lines.isdigit() else 50
            view_recent_logs(lines)
        elif choice == '2':
            view_requests_by_type()
        elif choice == '3':
            view_errors()
        elif choice == '4':
            view_successful_operations()
        elif choice == '5':
            view_webhook_details()
        elif choice == '6':
            print("👋 Tạm biệt!")
            break
        else:
            print("❌ Lựa chọn không hợp lệ")

if __name__ == "__main__":
    main() 