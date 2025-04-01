import imaplib
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取Gmail凭据
gmail_user = os.getenv("GMAIL_USERNAME")
gmail_pass = os.getenv("GMAIL_APP_PASSWORD")

print(f"正在测试Gmail连接: {gmail_user}")
print(f"应用密码长度: {len(gmail_pass)} 字符")

try:
    # 连接到Gmail
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(gmail_user, gmail_pass)
    
    # 列出邮箱
    status, mailboxes = mail.list()
    print(f"连接成功! 发现 {len(mailboxes)} 个邮箱")
    
    # 选择收件箱
    mail.select("inbox")
    status, messages = mail.search(None, "ALL")
    messages = messages[0].split()
    print(f"收件箱中有 {len(messages)} 封邮件")
    
    # 关闭连接
    mail.close()
    mail.logout()
    print("测试完成，Gmail连接正常")
    
except Exception as e:
    print(f"连接失败: {str(e)}") 