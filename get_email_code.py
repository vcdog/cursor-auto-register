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
import imaplib
import email
import os
from email.header import decode_header
from datetime import datetime, timedelta
from dotenv import load_dotenv


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
        elif self.email == "netease":
            info(
                f"初始化网易163邮箱验证器成功: {self.username}"
            )
        
        # 添加代理支持
        if use_proxy and EMAIL_PROXY_ENABLED:
            proxy = {
                "http": f"{EMAIL_PROXY_ADDRESS}",
                "https": f"{EMAIL_PROXY_ADDRESS}",
            }
            self.session.proxies.update(proxy)
            info(f"已启用代理: {EMAIL_PROXY_ADDRESS}")

        # Gmail配置
        self.gmail_username = GMAIL_USERNAME
        self.gmail_password = GMAIL_APP_PASSWORD
        
        # 网易163邮箱配置
        self.netease_username = os.environ.get("NETEASE_USERNAME", "")
        self.netease_password = os.environ.get("NETEASE_PASSWORD", "")
        
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
        # 添加诊断步骤
        if self.email == "netease":
            self.diagnose_email_setup()
        
        # 如果邮箱验证码获取方式为输入，则直接返回输入的验证码
        if EMAIL_CODE_TYPE == "INPUT":
            info("EMAIL_CODE_TYPE设为INPUT，跳过自动获取，直接手动输入")
            return self.prompt_manual_code()
        
        max_retries = max_retries or EMAIL_VERIFICATION_RETRIES
        wait_time = wait_time or EMAIL_VERIFICATION_WAIT
        info(f"开始获取邮箱验证码=>最大重试次数:{max_retries}, 等待时间:{wait_time}")
        
        # 验证邮箱类型是否支持
        if self.email not in ["tempemail", "zmail", "gmail", "netease"]:
            error(f"不支持的邮箱类型: {self.email}，支持的类型为: tempemail, zmail, gmail, netease")
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
                elif self.email == "netease":
                    code = self._get_netease_verification_code(source_email)
                
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
        """提示用户手动输入验证码"""
        print("\n" + "="*60)
        print("请打开邮箱 (可能在垃圾邮件文件夹) 查找来自Cursor的验证邮件")
        print("邮件标题通常为: [Cursor] Your verification code")
        print("验证码格式通常为6位数字")
        print("="*60 + "\n")
        
        while True:
            code = input("请输入验证码 (输入q退出): ")
            if code.lower() == 'q':
                return None
            
            if re.match(r'^\d{6}$', code):
                info(f"手动输入验证码: {code}")
                return code
            else:
                print("验证码格式不正确，请输入6位数字")

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
        """诊断邮箱设置"""
        info("开始诊断邮箱设置...")
        
        if self.email == "netease":
            info(f"当前邮箱类型: 网易163邮箱")
            info(f"使用的网易账号: {self.netease_username}")
            info(f"授权码前几位: {self.netease_password[:3]}***") # 只显示前三位
            
            # 尝试连接到网易邮箱服务器
            try:
                mail = imaplib.IMAP4_SSL("imap.163.com")
                info("网易163邮箱IMAP服务器连接成功")
                
                try:
                    mail.login(self.netease_username, self.netease_password)
                    info("网易163邮箱登录成功")
                    
                    try:
                        status, mailbox_data = mail.select("INBOX")
                        if status == 'OK':
                            info(f"选择收件箱成功: {mailbox_data}")
                            
                            # 尝试列出最近的几封邮件
                            result, data = mail.search(None, 'ALL')
                            if result == 'OK':
                                ids = data[0].split()
                                info(f"收件箱中共有 {len(ids)} 封邮件")
                                
                                if len(ids) > 0:
                                    info("尝试读取最新邮件...")
                                    latest_id = ids[-1]
                                    result, data = mail.fetch(latest_id, '(RFC822)')
                                    if result == 'OK':
                                        info("成功读取最新邮件")
                                    else:
                                        error(f"读取最新邮件失败: {result}")
                            else:
                                error(f"列出邮件失败: {result}")
                        else:
                            error(f"选择收件箱失败: {status}, {mailbox_data}")
                    except Exception as e:
                        error(f"选择收件箱或列出邮件时发生错误: {str(e)}")
                except Exception as e:
                    error(f"网易163邮箱登录失败: {str(e)}")
                finally:
                    try:
                        mail.logout()
                        info("网易163邮箱连接已关闭")
                    except:
                        pass
            except Exception as e:
                error(f"连接网易163邮箱服务器失败: {str(e)}")
        
        info("邮箱设置诊断完成")

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

    def _get_netease_verification_code(self, email_address, timeout=300):
        """从网易163邮箱获取验证码"""
        max_retries = 3  # 添加最大重试次数
        
        for retry in range(max_retries):
            try:
                # 使用IMAPClient而不是imaplib
                from imapclient import IMAPClient
                
                info(f"连接到网易163邮箱服务器... (尝试 {retry+1}/{max_retries})")
                server = IMAPClient("imap.163.com", ssl=True, port=993)
                
                # 登录
                info(f"正在登录网易邮箱: {self.netease_username}")
                server.login(self.netease_username, self.netease_password)
                
                # 发送ID命令
                info("发送客户端身份信息...")
                server.id_({"name": "IMAPClient", "version": "2.1.0", 
                           "vendor": "Mozilla", "contact": "support@cursor.so"})
                
                # 选择收件箱
                info("选择收件箱...")
                result = server.select_folder('INBOX')
                info(f"收件箱邮件数量: {result[b'EXISTS']}")
                
                # 设置搜索条件
                cutoff_time = (datetime.now() - timedelta(hours=1)).strftime("%d-%b-%Y")
                
                # 特定关键词搜索
                keywords = [
                    ['FROM', 'cursor'],
                    ['FROM', 'no-reply@cursor'],
                    ['SUBJECT', 'Verify your email'],
                    ['SUBJECT', 'verification code'],
                    ['SUBJECT', 'verify']
                ]
                
                # 创建OR搜索条件
                search_criteria = ['SINCE', cutoff_time, 'OR']
                for keyword in keywords:
                    search_criteria.extend(keyword)
                
                info(f"搜索条件: {search_criteria}")
                
                start_time = time.time()
                while time.time() - start_time < timeout:
                    # 首先尝试特定关键词搜索
                    message_ids = server.search(search_criteria)
                    info(f"找到 {len(message_ids)} 封匹配的邮件")
                    
                    # 如果没有找到邮件，使用宽松条件并限制为最近的10封
                    if not message_ids:
                        broader_criteria = ['SINCE', cutoff_time]
                        info(f"尝试更宽松的搜索条件: {broader_criteria}")
                        all_messages = server.search(broader_criteria)
                        # 只处理最近的10封邮件
                        message_ids = all_messages[-10:] if len(all_messages) > 10 else all_messages
                        info(f"使用宽松条件找到 {len(message_ids)} 封邮件")
                    
                    if message_ids:
                        # 从最新邮件开始检查
                        for msg_id in sorted(message_ids, reverse=True):
                            try:
                                # 获取邮件内容
                                fetched = server.fetch([msg_id], ['ENVELOPE', 'BODY[]'])
                                raw_email = fetched[msg_id][b'BODY[]']
                                envelope = fetched[msg_id][b'ENVELOPE']
                                
                                # 解析邮件
                                msg = email.message_from_bytes(raw_email)
                                
                                # 解析主题和发件人
                                subject = ''
                                if envelope.subject:
                                    if isinstance(envelope.subject, bytes):
                                        subject = envelope.subject.decode('utf-8', errors='replace')
                                    else:
                                        subject = str(envelope.subject)
                                
                                sender = ''
                                if envelope.from_ and len(envelope.from_) > 0:
                                    addr = envelope.from_[0]
                                    email_parts = []
                                    if addr.mailbox:
                                        mailbox = addr.mailbox.decode('utf-8', errors='replace') if isinstance(addr.mailbox, bytes) else addr.mailbox
                                        email_parts.append(mailbox)
                                    if addr.host:
                                        host = addr.host.decode('utf-8', errors='replace') if isinstance(addr.host, bytes) else addr.host
                                        email_parts.append(host)
                                    
                                    if email_parts:
                                        if len(email_parts) == 2:
                                            sender = f"{email_parts[0]}@{email_parts[1]}"
                                        else:
                                            sender = email_parts[0]
                                
                                info(f"检查邮件 - 发件人: {sender} | 主题: {subject}")
                                
                                # 提取邮件正文
                                body = ""
                                if msg.is_multipart():
                                    for part in msg.walk():
                                        content_type = part.get_content_type()
                                        if content_type == "text/plain" or content_type == "text/html":
                                            try:
                                                body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                                                break
                                            except:
                                                pass
                                else:
                                    try:
                                        body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                                    except:
                                        pass
                                
                                # 预览邮件内容
                                preview = body[:200] + "..." if len(body) > 200 else body
                                info(f"邮件内容预览: {preview}")
                                
                                # 使用改进的验证码提取算法
                                verification_code = self._extract_cursor_verification_code(body)
                                if verification_code:
                                    info(f"找到验证码: {verification_code}")
                                    server.logout()
                                    return verification_code
                            except Exception as e:
                                info(f"处理邮件时出错: {str(e)}")
                                continue
                    
                    # 等待后重试
                    info(f"未找到验证码，等待 {EMAIL_VERIFICATION_WAIT} 秒后重试...")
                    time.sleep(EMAIL_VERIFICATION_WAIT)
                
                # 超时后关闭连接
                info("未找到验证码")
                server.logout()
                return None
                
            except Exception as e:
                error(f"获取网易邮箱验证码时发生错误: {str(e)}")
                if retry < max_retries - 1:
                    info(f"5秒后重试... ({retry+1}/{max_retries})")
                    time.sleep(5)
                else:
                    return None
        
        return None

    def _extract_cursor_verification_code(self, text):
        """专门为Cursor验证邮件提取验证码"""
        # 查找常见格式的验证码提示
        code_indicators = [
            "verification code",
            "your code",
            "enter the code",
            "code below",
            "your verification code",
            "验证码"
        ]
        
        # 先检查邮件内容中是否有这些提示语
        indicator_found = False
        for indicator in code_indicators:
            if indicator.lower() in text.lower():
                indicator_found = True
                break
        
        if indicator_found:
            # 使用更精确的模式匹配验证码
            patterns = [
                # 针对"Enter the code below"格式
                r'code below[^\d]*(\d{6})',
                # 针对"Your verification code is: 123456"格式
                r'verification code[^\d]*(\d{6})',
                # 针对"Your code: 123456"格式
                r'your code[^\d]*(\d{6})',
                # 一般6位数字格式，但更严格的匹配
                r'[\s:](\d{6})[\s\n\r\.]',
                # 最后才是简单的6位数字匹配
                r'(\d{6})'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    return matches[0]
        
        return None

    def _decode_email_header(self, header_text):
        """解码邮件头信息"""
        decoded_parts = decode_header(header_text)
        decoded_text = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    decoded_text += part.decode(encoding)
                else:
                    try:
                        decoded_text += part.decode('utf-8')
                    except:
                        try:
                            decoded_text += part.decode('latin-1')
                        except:
                            decoded_text += str(part)
            else:
                decoded_text += part
                
        return decoded_text

    def _handle_netease_security_issue(self):
        """处理网易邮箱安全限制问题"""
        error("网易163邮箱安全限制：无法访问收件箱")
        print("\n" + "="*60)
        print("网易163邮箱安全限制问题解决方法：")
        print("1. 登录网易163邮箱网页版：https://mail.163.com")
        print("2. 点击'设置' -> 'POP3/SMTP/IMAP'")
        print("3. 确保IMAP服务已开启")
        print("4. 删除现有授权码，重新生成授权码")
        print("5. 在'设置' -> '邮箱安全设置'中，检查是否有异常登录提醒")
        print("6. 在'设置' -> '反垃圾'中，将此应用所在设备的IP添加到白名单")
        print("7. 更新.env文件中的NETEASE_PASSWORD为新的授权码")
        print("="*60 + "\n")
        
        response = input("您是否已完成上述步骤？(y/n): ")
        return response.lower() == 'y'

    def _handle_netease_security_issue_and_retry(self, email_address, timeout):
        """处理安全限制并重试获取验证码"""
        if self._handle_netease_security_issue():
            # 重新加载环境变量获取更新后的密码
            load_dotenv(override=True)
            # 更新密码
            self.netease_password = os.environ.get("NETEASE_PASSWORD", "")
            info(f"已重新加载授权码: {self.netease_password[:3]}***")
            # 重新尝试获取验证码
            return self._get_netease_verification_code(email_address, timeout)
        else:
            # 切换到手动模式
            info("由于网易邮箱安全限制，切换到手动输入验证码模式")
            return self.prompt_manual_code()

    def _secure_netease_login(self, mail_server):
        """使用更安全的方式登录网易邮箱"""
        try:
            # 1. 发送ID命令以模拟合法客户端
            mail_server._simple_command('ID', '("name" "Mozilla" "version" "20.0" "vendor" "Mozilla" "contact" "mozilla.org")')
            mail_server.readline()
            
            # 2. 使用SSL连接
            if not isinstance(mail_server, imaplib.IMAP4_SSL):
                info("转换为SSL连接...")
                mail_server.starttls()
            
            # 3. 尝试登录
            mail_server.login(self.netease_username, self.netease_password)
            info("网易邮箱登录成功")
            return True
        except Exception as e:
            error(f"网易邮箱安全登录失败: {str(e)}")
            return False

    def _reconnect_netease(self):
        """重新连接网易邮箱IMAP服务器"""
        try:
            # 使用更安全的连接方式
            mail = imaplib.IMAP4_SSL("imap.163.com", 993)
            
            # 尝试先执行NOOP命令建立连接
            mail.noop()
            
            # 使用安全登录方法
            if self._secure_netease_login(mail):
                # 选择收件箱
                status, _ = mail.select("INBOX")
                if status == 'OK':
                    info("网易邮箱重新连接成功")
                    return mail
            
            # 如果仍然失败，关闭连接
            try:
                mail.logout()
            except:
                pass
            
            return None
        except Exception as e:
            error(f"重新连接网易邮箱失败: {str(e)}")
            return None

    def test_netease_connection(self):
        """测试网易邮箱连接是否可用"""
        info("测试网易邮箱连接...")
        
        try:
            # 尝试使用不同的连接方式
            connection_methods = [
                {"type": "SSL", "port": 993, "class": imaplib.IMAP4_SSL},
                {"type": "普通+STARTTLS", "port": 143, "class": imaplib.IMAP4}
            ]
            
            for method in connection_methods:
                info(f"尝试 {method['type']} 连接, 端口 {method['port']}...")
                
                try:
                    if method["type"] == "SSL":
                        mail = method["class"]("imap.163.com", method["port"])
                    else:
                        mail = method["class"]("imap.163.com", method["port"])
                        mail.starttls()
                    
                    # 尝试安全登录
                    if self._secure_netease_login(mail):
                        status, _ = mail.select("INBOX")
                        if status == 'OK':
                            info(f"✅ {method['type']} 连接成功!")
                            mail.logout()
                            return True
                        else:
                            info(f"❌ {method['type']} 连接失败: 无法选择收件箱")
                    
                    try:
                        mail.logout()
                    except:
                        pass
                except Exception as e:
                    info(f"❌ {method['type']} 连接失败: {str(e)}")
            
            error("所有连接方式均失败，请检查网络和账号设置")
            return False
        except Exception as e:
            error(f"测试连接时发生错误: {str(e)}")
            return False

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
    parser.add_argument('--type', default=EMAIL_TYPE, choices=['tempemail', 'zmail', 'gmail', 'netease'], help='邮箱类型')
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
