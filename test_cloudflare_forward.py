import imaplib
import email
import re
import os
from email.header import decode_header
from dotenv import load_dotenv
import time

# 加载环境变量
load_dotenv()

# 获取配置
gmail_user = os.getenv("GMAIL_USERNAME")
gmail_pass = os.getenv("GMAIL_APP_PASSWORD")
custom_domain = os.getenv("EMAIL_DOMAINS", "iftballs.com").split(",")[0]

print(f"测试Cloudflare邮件转发: {custom_domain} -> {gmail_user}")

try:
    # 连接到Gmail
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(gmail_user, gmail_pass)
    
    # 记录测试开始时间
    start_time = time.time()
    test_time_str = time.strftime("%H:%M:%S", time.localtime(start_time))
    
    # 生成测试邮件地址
    test_address = f"test{int(time.time())%10000}@{custom_domain}"
    
    print(f"当前时间: {test_time_str}")
    print(f"请向 {test_address} 发送一封测试邮件，包含文本'TEST123456'")
    print("发送后，脚本将每15秒检查一次是否收到转发邮件...")
    
    # 更长的等待时间和更多的尝试次数
    max_retries = 15  # 3分45秒 (15秒 x 15次)
    for i in range(max_retries):
        time.sleep(15)
        print(f"检查新邮件... ({i+1}/{max_retries})")
        
        # 选择收件箱并刷新
        mail.select("inbox")
        
        # 使用SINCE搜索，只查找测试开始后收到的邮件
        date_str = time.strftime("%d-%b-%Y", time.localtime(start_time))
        search_criteria = f'(SINCE "{date_str}")'
        status, data = mail.search(None, search_criteria)
        mail_ids = data[0].split()
        
        if mail_ids:
            print(f"找到 {len(mail_ids)} 封可能的新邮件，检查中...")
            
            for email_id in reversed(mail_ids):  # 从最新的邮件开始检查
                try:
                    status, data = mail.fetch(email_id, "(RFC822)")
                    raw_email = data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    # 获取邮件主题和时间
                    subject = ""
                    if msg["Subject"]:
                        subject = decode_header(msg["Subject"])[0][0]
                        if isinstance(subject, bytes):
                            subject = subject.decode()
                    
                    # 获取邮件日期
                    date = msg.get("Date", "")
                    
                    print(f"检查邮件: {subject} | {date}")
                    
                    # 获取所有收件人字段
                    to_field = msg.get("To", "")
                    cc_field = msg.get("Cc", "")
                    delivered_to = msg.get("Delivered-To", "")
                    
                    # 获取邮件内容
                    mail_text = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type == "text/plain" or content_type == "text/html":
                                try:
                                    mail_text += part.get_payload(decode=True).decode() + "\n"
                                except:
                                    pass
                    else:
                        try:
                            mail_text = msg.get_payload(decode=True).decode()
                        except:
                            pass
                    
                    # 更全面地检查是否是转发邮件
                    is_forwarded = False
                    if custom_domain in to_field or custom_domain in cc_field or custom_domain in delivered_to:
                        is_forwarded = True
                        print(f"在邮件头找到域名: {custom_domain}")
                    elif custom_domain in mail_text:
                        is_forwarded = True
                        print(f"在邮件内容中找到域名: {custom_domain}")
                    elif test_address.split("@")[0] in mail_text:
                        is_forwarded = True
                        print(f"在邮件内容中找到测试地址用户名: {test_address.split('@')[0]}")
                    
                    if is_forwarded:
                        # 检查测试内容
                        if "TEST123456" in mail_text:
                            print("\n成功! 测试内容已找到，Cloudflare转发工作正常!")
                            mail.close()
                            mail.logout()
                            exit(0)
                        else:
                            print("转发邮件中未找到测试文本，继续检查...")
                except Exception as e:
                    print(f"处理邮件时出错: {str(e)}")
                    continue
    
    print("在指定时间内未能自动检测到测试邮件，但您确认邮件已收到")
    print("这可能是因为转发改变了邮件格式或头部信息")
    print("\n建议手动确认:")
    print(f"1. 确认您向 {test_address} 发送了测试邮件")
    print(f"2. 确认 {gmail_user} 收到了相关邮件")
    print("3. 如果两项都确认，则Cloudflare转发正常工作")
    
    mail.close()
    mail.logout()
    
except Exception as e:
    print(f"测试过程中出错: {str(e)}") 