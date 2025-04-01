from logger import info, error
# 添加warn函数作为info的包装
def warn(message):
    """警告日志函数"""
    info(f"警告: {message}")

import time
import re
import requests
from config import (
    EMAIL_USERNAME,
    EMAIL_DOMAIN,
    EMAIL_PIN,
    EMAIL_VERIFICATION_RETRIES,
    EMAIL_VERIFICATION_WAIT,
    EMAIL_TYPE,
    EMAIL_PROXY_ADDRESS,
    EMAIL_PROXY_ENABLED,
    EMAIL_API,
    EMAIL_CODE_TYPE,
    GMAIL_USERNAME,
    GMAIL_APP_PASSWORD,
    EMAIL_DOMAINS
)


class EmailVerificationHandler:
    def __init__(self, username=None, domain=None, pin=None, use_proxy=False):
        self.email = EMAIL_TYPE
        self.username = username or EMAIL_USERNAME
        self.domain = domain or EMAIL_DOMAIN
        self.session = requests.Session()
        self.emailApi = EMAIL_API
        self.emailExtension = self.domain
        self.pin = pin or EMAIL_PIN
        if self.pin == "":
            info("注意: 邮箱PIN码为空")
        if self.email == "tempemail":
            info(
                f"初始化邮箱验证器成功: {self.username}@{self.domain} pin: {self.pin}"
            )
        elif self.email == "zmail":
            info(
                f"初始化邮箱验证器成功: {self.emailApi}"
            )
        elif self.email == "gmail":
            info(
                f"初始化Gmail邮箱验证器成功: {self.username}"
            )
        
        # 添加代理支持
        if use_proxy and EMAIL_PROXY_ENABLED:
            proxy = {
                "http": f"{EMAIL_PROXY_ADDRESS}",
                "https": f"{EMAIL_PROXY_ADDRESS}",
            }
            self.session.proxies.update(proxy)
            info(f"已启用代理: {EMAIL_PROXY_ADDRESS}")

    def check(self):
        mail_list_url = f"https://tempmail.plus/api/mails?email={self.username}%40{self.domain}&limit=20&epin={self.pin}"
        try:
            # 增加超时时间并添加错误重试
            for retry in range(3):
                try:
                    info(f"请求URL (尝试 {retry+1}/3): {mail_list_url}")
                    mail_list_response = self.session.get(mail_list_url, timeout=30)  # 增加超时时间到30秒
                    mail_list_data = mail_list_response.json()
                    time.sleep(0.5)
                    
                    # 修正判断逻辑：当result为true时才是成功
                    if mail_list_data.get("result") == True:
                        info(f"成功获取邮件列表数据: 共{mail_list_data.get('count', 0)}封邮件")
                        return True
                    else:
                        error(f"API返回结果中无result字段或result为false: {mail_list_data}")
                        return False
                    
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    if retry < 2:  # 如果不是最后一次尝试
                        warn(f"请求超时或连接错误，正在重试... ({retry+1}/3)")
                        time.sleep(2)  # 增加重试间隔
                    else:
                        raise  # 最后一次尝试失败，抛出异常
        except requests.exceptions.Timeout:
            error("获取邮件列表超时")
        except requests.exceptions.ConnectionError:
            error("获取邮件列表连接错误")
            info(f'{mail_list_url}')
        except Exception as e:
            error(f"获取邮件列表发生错误: {str(e)}")
        return False

    def get_verification_code(
        self, source_email=None, max_retries=None, wait_time=None
    ):
        """
        获取验证码，增加了重试机制

        Args:
            max_retries: 最大重试次数
            wait_time: 每次重试间隔时间(秒)

        Returns:
            str: 验证码或None
        """
        # 如果邮箱验证码获取方式为输入，则直接返回输入的验证码
        if EMAIL_CODE_TYPE == "INPUT":
            info("EMAIL_CODE_TYPE设为INPUT，跳过自动获取，直接手动输入")
            return self.prompt_manual_code()
        
        max_retries = max_retries or EMAIL_VERIFICATION_RETRIES
        wait_time = wait_time or EMAIL_VERIFICATION_WAIT
        info(f"开始获取邮箱验证码=>最大重试次数:{max_retries}, 等待时间:{wait_time}")
        
        # 验证邮箱类型是否支持
        if self.email not in ["tempemail", "zmail", "gmail"]:
            error(f"不支持的邮箱类型: {self.email}，支持的类型为: tempemail, zmail, gmail")
            warn("自动切换到手动输入模式")
            return self.prompt_manual_code()
        
        for attempt in range(max_retries):
            try:
                info(f"当前EMail类型为： {self.email}")
                code = None
                mail_id = None
                
                if self.email == "tempemail":
                    code, mail_id = self.get_tempmail_email_code(source_email)
                elif self.email == "zmail":
                    code, mail_id = self.get_zmail_email_code(source_email)
                elif self.email == "gmail":
                    code, mail_id = self.get_gmail_email_code(source_email)
                
                if code:
                    info(f"成功获取验证码: {code}")
                    return code
                elif attempt < max_retries - 1:
                    info(f"未找到验证码，{wait_time}秒后重试 ({attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                else:
                    info(f"已达到最大重试次数({max_retries})，未找到验证码")
            except Exception as e:
                error(f"获取验证码失败: {str(e)}")
                if attempt < max_retries - 1:
                    info(f"将在{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    error(f"已达到最大重试次数({max_retries})，获取验证码失败")

        # 所有自动尝试都失败后，询问是否手动输入
        response = input("自动获取验证码失败，是否手动输入? (y/n): ").lower()
        if response == 'y':
            return self.prompt_manual_code()
        return None

    # 手动输入验证码
    def prompt_manual_code(self):
        """手动输入验证码"""
        info("自动获取验证码失败，开始手动输入验证码。")
        code = input("输入6位数字验证码: ").strip()
        return code

    def get_tempmail_email_code(self, source_email=None):
        info("开始获取邮件列表")
        # 获取邮件列表
        mail_list_url = f"https://tempmail.plus/api/mails?email={self.username}%40{self.domain}&limit=20&epin={self.pin}"
        try:
            # 增加错误重试和超时时间
            for retry in range(3):
                try:
                    info(f"请求邮件列表 (尝试 {retry+1}/3): {mail_list_url}")
                    mail_list_response = self.session.get(
                        mail_list_url, timeout=30
                    )
                    mail_list_data = mail_list_response.json()
                    time.sleep(0.5)
                    
                    # 修正判断逻辑
                    if mail_list_data.get("result") == True:
                        info(f"成功获取邮件列表: 共{mail_list_data.get('count', 0)}封邮件")
                        # 继续处理
                    else:
                        error(f"API返回失败结果: {mail_list_data}")
                        return None, None
                    
                    break  # 成功获取数据，跳出重试循环
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    if retry < 2:  # 如果不是最后一次尝试
                        warn(f"请求超时或连接错误，正在重试... ({retry+1}/3)")
                        time.sleep(2 * (retry + 1))  # 递增的等待时间
                    else:
                        raise  # 最后一次尝试失败，抛出异常
        
            # 获取最新邮件的ID
            first_id = mail_list_data.get("first_id")
            if not first_id:
                return None, None
            info(f"开始获取邮件详情: {first_id}")
            # 获取具体邮件内容
            mail_detail_url = f"https://tempmail.plus/api/mails/{first_id}?email={self.username}%40{self.domain}&epin={self.pin}"
            try:
                mail_detail_response = self.session.get(
                    mail_detail_url, timeout=10
                )  # 添加超时参数
                mail_detail_data = mail_detail_response.json()
                time.sleep(0.5)
                if mail_detail_data.get("result") == False:
                    error(f"获取邮件详情失败: {mail_detail_data}")
                    return None, None
            except requests.exceptions.Timeout:
                error("获取邮件详情超时")
                return None, None
            except requests.exceptions.ConnectionError:
                error("获取邮件详情连接错误")
                return None, None
            except Exception as e:
                error(f"获取邮件详情发生错误: {str(e)}")
                return None, None

            # 从邮件文本中提取6位数字验证码
            mail_text = mail_detail_data.get("text", "")

            # 如果提供了source_email，确保邮件内容中包含该邮箱地址
            if source_email and source_email.lower() not in mail_text.lower():
                error(f"邮件内容不包含指定的邮箱地址: {source_email}")
            else:
                info(f"邮件内容包含指定的邮箱地址: {source_email}")

            code_match = re.search(r"(?<![a-zA-Z@.])\b\d{6}\b", mail_text)

            if code_match:
                # 清理邮件
                self._cleanup_mail(first_id)
                return code_match.group(), first_id
            return None, None
        except requests.exceptions.Timeout:
            error("获取邮件列表超时")
            return None, None
        except requests.exceptions.ConnectionError:
            error("获取邮件列表连接错误")
            return None, None
        except Exception as e:
            error(f"获取邮件列表发生错误: {str(e)}")
            return None, None

    def _cleanup_mail(self, first_id):
        # 构造删除请求的URL和数据
        delete_url = "https://tempmail.plus/api/mails/"
        payload = {
            "email": f"{self.username}@{self.domain}",
            "first_id": first_id,
            "epin": self.pin,
        }

        # 最多尝试3次
        for _ in range(3):
            response = self.session.delete(delete_url, data=payload)
            try:
                result = response.json().get("result")
                if result is True:
                    return True
            except:
                pass

            # 如果失败,等待0.2秒后重试
            time.sleep(0.2)

        return False

    # 如果是zmail 需要先创建邮箱
    def create_zmail_email(account_info):
        # 如果邮箱类型是zmail 需要先创建邮箱
        session = requests.Session()
        if EMAIL_PROXY_ENABLED:
            proxy = {
                "http": f"{EMAIL_PROXY_ADDRESS}",
                "https": f"{EMAIL_PROXY_ADDRESS}",
            }
            session.proxies.update(proxy)
        # 创建临时邮箱URL
        create_url = f"{EMAIL_API}/api/mailboxes"
        username = account_info["email"].split("@")[0]
        # 生成临时邮箱地址
        payload = {
            "address": f"{username}",
            "expiresInHours": 24,
        }
        # 发送POST请求创建临时邮箱
        try:
            create_response = session.post(
                create_url, json=payload, timeout=100
            )  # 添加超时参数
            info(f"创建临时邮箱成功: {create_response.status_code}")
            create_data = create_response.json()
            info(f"创建临时邮箱返回数据: {create_data}")
            # 检查创建邮箱是否成功
            time.sleep(0.5)
            if create_data.get("success") is True or create_data.get('error') == '邮箱地址已存在':
                info(f"邮箱创建成功: {create_data}")
            else:
                error(f"邮箱创建失败: {create_data}")
                return None, None
        except requests.exceptions.Timeout:
            error("创建临时邮箱超时", create_url)
            return None, None
        info(f"创建临时邮箱成功: {create_data}, 返回值: {create_data}")
            
    # 获取zmail邮箱验证码
    def get_zmail_email_code(self, source_email=None):
        info("开始获取邮件列表")
        # 获取邮件列表
        username = source_email.split("@")[0]
        mail_list_url = f"{EMAIL_API}/api/mailboxes/{username}/emails"
        proxy = {
                "http": f"{EMAIL_PROXY_ADDRESS}",
                "https": f"{EMAIL_PROXY_ADDRESS}",
            }
        self.session.proxies.update(proxy)
        try:
            mail_list_response = self.session.get(
                mail_list_url, timeout=10000
            )  # 添加超时参数
            mail_list_data = mail_list_response.json()
            time.sleep(2)
            if not mail_list_data.get("emails"):
                return None, None
        except requests.exceptions.Timeout:
            error("获取邮件列表超时")
            return None, None
        except requests.exceptions.ConnectionError:
            error("获取邮件列表连接错误")
            return None, None
        except Exception as e:
            error(f"获取邮件列表发生错误: {str(e)}")
            return None, None

        # 获取最新邮件的ID、
        mail_detail_data_len = len(mail_list_data["emails"])
        if mail_detail_data_len == 0:
            return None, None
        mail_list_data = mail_list_data["emails"][0]
        # 获取最新邮件的ID
        mail_id = mail_list_data.get("id")
        if not mail_id:
            return None, None
        # 获取具体邮件内容
        mail_detail_url = f"{EMAIL_API}/api/emails/{mail_id}"
        returnData = ''
        try:
            mail_detail_response = self.session.get(
                mail_detail_url, timeout=10
            )  # 添加超时参数
            returnData = mail_detail_response.json()
            time.sleep(2)
        except requests.exceptions.Timeout:
            error("获取邮件详情超时")
            return None, None
        except requests.exceptions.ConnectionError:
            error("获取邮件详情连接错误")
            return None, None
        except Exception as e:
            error(f"获取邮件详情发生错误: {str(e)}")
            return None, None

        # 从邮件文本中提取6位数字验证码\
        mail_text = returnData.get("email")
        mail_text = mail_text.get("textContent")
        # 如果提供了source_email，确保邮件内容中包含该邮箱地址
        if source_email and source_email.lower() not in mail_text.lower():
            error(f"邮件内容不包含指定的邮箱地址: {source_email}")
        else:
            info(f"邮件内容包含指定的邮箱地址: {source_email}")

        code_match = re.search(r"(?<![a-zA-Z@.])\b\d{6}\b", mail_text)
        info(f"验证码匹配结果: {code_match}")
        # 如果找到验证码, 返回验证码和邮件ID
        if code_match:
            return code_match.group(), mail_id
        else:
            error("未找到验证码")
            return None, None

    def diagnose_email_setup(self):
        """诊断邮箱设置并显示可能的问题"""
        issues = []
        
        # 检查邮箱类型
        if self.email not in ["tempemail", "zmail", "gmail"]:
            issues.append(f"不支持的邮箱类型: {self.email}")
        
        # 检查邮箱用户名
        if not self.username:
            issues.append("邮箱用户名为空")
        
        # 检查域名
        if not self.domain and self.email != "gmail":
            issues.append("邮箱域名为空")
        
        # Gmail类型使用完整用户名
        email_address = self.username
        if self.email == "gmail":
            if "@" not in self.username:
                # 使用配置中的DOMAINS的第一个域名
                email_address = f"{self.username}@{EMAIL_DOMAINS[0]}"
        else:
            email_address = f"{self.username}@{self.domain}"
        
        # 检查获取验证码类型
        if EMAIL_CODE_TYPE == "INPUT":
            issues.append("EMAIL_CODE_TYPE设为INPUT，将跳过自动获取")
        
        info("----- 邮箱设置诊断 -----")
        info(f"邮箱类型: {self.email}")
        info(f"邮箱地址: {email_address}")
        info(f"验证码获取方式: {EMAIL_CODE_TYPE}")
        
        if issues:
            warn("发现以下问题:")
            for issue in issues:
                warn(f"- {issue}")
        else:
            info("未发现明显问题")
        
        return issues

    # 获取Gmail邮箱验证码
    def get_gmail_email_code(self, source_email=None):
        import imaplib
        import email
        from email.header import decode_header
        import os
        import re
        import traceback
        import socket
        import time
        from config import GMAIL_USERNAME, GMAIL_APP_PASSWORD
        
        info("开始从Gmail获取转发的验证码邮件")
        
        # 连接重试次数
        max_conn_retries = 3
        
        for conn_retry in range(max_conn_retries):
            try:
                # 连接到Gmail IMAP服务器
                info(f"尝试连接Gmail服务器 (尝试 {conn_retry+1}/{max_conn_retries})")
                mail = imaplib.IMAP4_SSL("imap.gmail.com", timeout=30)  # 设置30秒超时
                mail.login(GMAIL_USERNAME, GMAIL_APP_PASSWORD)
                mail.select("inbox")
                
                # 搜索最近的邮件 - 增加到最近20封
                status, data = mail.search(None, "ALL")
                mail_ids = data[0].split()
                
                if not mail_ids:
                    info("Gmail邮箱为空")
                    return None, None
                
                # 获取最近的20封邮件
                recent_email_ids = mail_ids[-20:] if len(mail_ids) > 20 else mail_ids
                info(f"准备检查最近的 {len(recent_email_ids)} 封邮件")
                
                # 从最新到最旧逐一查看邮件
                for email_id in reversed(recent_email_ids):
                    try:
                        status, data = mail.fetch(email_id, "(RFC822)")
                        
                        # 解析邮件内容
                        raw_email = data[0][1]
                        msg = email.message_from_bytes(raw_email)
                        
                        subject = ""
                        # 获取邮件主题
                        if msg["Subject"]:
                            subject = decode_header(msg["Subject"])[0][0]
                            if isinstance(subject, bytes):
                                subject = subject.decode()
                        
                        info(f"检查邮件: {subject}")
                        
                        # 获取邮件正文 - 同时检查文本和HTML内容
                        mail_text = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))
                                
                                try:
                                    if "attachment" not in content_disposition:
                                        if content_type == "text/plain":
                                            mail_text += part.get_payload(decode=True).decode() + "\n"
                                        elif content_type == "text/html":
                                            # 简单处理HTML内容以提取文本
                                            html_content = part.get_payload(decode=True).decode()
                                            mail_text += html_content + "\n"
                                except Exception as e:
                                    info(f"解析邮件部分时出错: {str(e)}")
                                    continue
                        else:
                            try:
                                mail_text = msg.get_payload(decode=True).decode()
                            except:
                                info("无法解码邮件内容")
                        
                        # 验证邮件来源，检查更多关键词
                        cursor_keywords = ["cursor", "verification", "verify", "code", "验证码"]
                        is_cursor_email = False
                        
                        for keyword in cursor_keywords:
                            if keyword.lower() in mail_text.lower() or keyword.lower() in subject.lower():
                                is_cursor_email = True
                                info(f"找到疑似Cursor相关邮件 (关键词: {keyword})")
                                break
                        
                        if is_cursor_email:
                            # 尝试多种验证码匹配模式
                            code_patterns = [
                                r"(?<![a-zA-Z@.])\b\d{6}\b",  # 标准6位数字
                                r"验证码[：:]\s*(\d{6})",      # 中文格式
                                r"code[：:]\s*(\d{6})",        # 英文格式
                                r"verification code[：:]\s*(\d{6})",  # 完整英文
                            ]
                            
                            for pattern in code_patterns:
                                code_match = re.search(pattern, mail_text)
                                if code_match:
                                    # 获取匹配组或整个匹配
                                    code = code_match.group(1) if len(code_match.groups()) > 0 else code_match.group()
                                    info(f"找到验证码: {code}")
                                    mail.close()
                                    mail.logout()
                                    return code, email_id.decode()
                
                    except Exception as e:
                        info(f"处理邮件时出错: {str(e)}")
                        continue
                
                info("未在最近邮件中找到验证码")
                mail.close()
                mail.logout()
                return None, None
                
            except (socket.timeout, socket.error, ConnectionError) as e:
                error(f"Gmail连接超时或错误 (尝试 {conn_retry+1}/{max_conn_retries}): {str(e)}")
                if conn_retry < max_conn_retries - 1:
                    info("5秒后重试连接...")
                    time.sleep(5)
                else:
                    error("已达到最大连接尝试次数，放弃")
                    return None, None
            except Exception as e:
                error(f"获取Gmail验证码失败: {str(e)}")
                traceback.print_exc()
                return None, None

if __name__ == "__main__":
    import argparse
    
    # 添加代码检查并显示配置值
    info(f"当前配置: EMAIL_TYPE={EMAIL_TYPE}, EMAIL_CODE_TYPE={EMAIL_CODE_TYPE}")
    
    # 如果EMAIL_CODE_TYPE为INPUT则警告用户
    if EMAIL_CODE_TYPE == "INPUT":
        warn("EMAIL_CODE_TYPE设为INPUT将会跳过自动获取验证码，直接手动输入")
        # 给用户选择是否临时更改为自动模式
        response = input("是否临时更改为自动模式? (y/n): ").lower()
        if response == 'y':
            EMAIL_CODE_TYPE = "AUTO"
            info("已临时更改为自动模式")
    
    parser = argparse.ArgumentParser(description='测试邮箱验证码获取功能')
    parser.add_argument('--username', default=EMAIL_USERNAME, help='邮箱用户名')
    parser.add_argument('--domain', default=EMAIL_DOMAIN, help='邮箱域名')
    parser.add_argument('--pin', default=EMAIL_PIN, help='邮箱PIN码（可以为空）')
    parser.add_argument('--source', help='来源邮箱（可选）')
    parser.add_argument('--type', default=EMAIL_TYPE, choices=['tempemail', 'zmail', 'gmail'], help='邮箱类型')
    parser.add_argument('--proxy', action='store_true', help='是否使用代理')
    args = parser.parse_args()
    
    # 覆盖全局EMAIL_TYPE以便测试不同类型
    from config import EMAIL_TYPE
    if args.type != EMAIL_TYPE:
        info(f"覆盖EMAIL_TYPE从{EMAIL_TYPE}到{args.type}")
        EMAIL_TYPE = args.type
    
    # 创建邮箱验证处理器
    handler = EmailVerificationHandler(
        username=args.username, 
        domain=args.domain, 
        pin=args.pin,
        use_proxy=args.proxy
    )
    
    # 诊断邮箱设置
    handler.diagnose_email_setup()
    
    # 测试检查邮箱
    info("测试检查邮箱...")
    check_result = handler.check()
    info(f"检查结果: {'成功' if check_result else '失败'}")
    
    # 测试获取验证码
    info("测试获取验证码...")
    code = handler.get_verification_code(source_email=args.source)
    
    if code:
        info(f"成功获取验证码: {code}")
    else:
        error("获取验证码失败")
    
    info("测试完成")
