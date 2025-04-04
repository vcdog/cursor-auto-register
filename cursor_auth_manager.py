import sqlite3
import os
import sys
from selenium import webdriver
import time


class CursorAuthManager:
    """Cursor认证信息管理器"""

    def __init__(self):
        # 判断操作系统
        if sys.platform == "win32":  # Windows
            appdata = os.getenv("APPDATA")
            if appdata is None:
                raise EnvironmentError("APPDATA 环境变量未设置")
            self.db_path = os.path.join(
                appdata, "Cursor", "User", "globalStorage", "state.vscdb"
            )
        elif sys.platform == "darwin":  # macOS
            self.db_path = os.path.abspath(
                os.path.expanduser(
                    "~/Library/Application Support/Cursor/User/globalStorage/state.vscdb"
                )
            )
        elif sys.platform == "linux":  # Linux 和其他类Unix系统
            self.db_path = os.path.abspath(
                os.path.expanduser("~/.config/Cursor/User/globalStorage/state.vscdb")
            )
        else:
            raise NotImplementedError(f"不支持的操作系统: {sys.platform}")
        
        # 初始化日志记录器
        import logging
        self.logger = logging.getLogger("cursor_auth_manager")
        self.turnstile_path = ""  # 初始化插件路径

    def update_auth(self, email=None, access_token=None, refresh_token=None):
        """
        更新Cursor的认证信息
        :param email: 新的邮箱地址
        :param access_token: 新的访问令牌
        :param refresh_token: 新的刷新令牌
        :return: bool 是否成功更新
        """
        updates = []
        # 登录状态
        updates.append(("cursorAuth/cachedSignUpType", "Auth_0"))

        if email is not None:
            updates.append(("cursorAuth/cachedEmail", email))
        if access_token is not None:
            updates.append(("cursorAuth/accessToken", access_token))
        if refresh_token is not None:
            updates.append(("cursorAuth/refreshToken", refresh_token))

        if not updates:
            print("没有提供任何要更新的值")
            return False

        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for key, value in updates:
                # 如果没有更新任何行,说明key不存在,执行插入
                # 检查 accessToken 是否存在
                check_query = "SELECT COUNT(*) FROM itemTable WHERE key = ?"
                cursor.execute(check_query, (key,))
                if cursor.fetchone()[0] == 0:
                    insert_query = "INSERT INTO itemTable (key, value) VALUES (?, ?)"
                    cursor.execute(insert_query, (key, value))
                else:
                    update_query = "UPDATE itemTable SET value = ? WHERE key = ?"
                    cursor.execute(update_query, (value, key))

                if cursor.rowcount > 0:
                    print(f"成功更新 {key.split('/')[-1]} ： {value}")
                else:
                    print(f"未找到 {key.split('/')[-1]} 或值未变化")

            conn.commit()
            return True

        except sqlite3.Error as e:
            print("数据库错误:", str(e))
            return False
        except Exception as e:
            print("发生错误:", str(e))
            return False
        finally:
            if conn:
                conn.close()

    def initialize_browser(self):
        """初始化浏览器"""
        try:
            self.logger.info("正在初始化浏览器...")
            self.logger.info(f"插件路径: {self.turnstile_path}")
            
            # 从环境变量或配置中获取浏览器路径
            browser_path = os.environ.get('BROWSER_PATH')
            
            # 设置固定的User-Agent
            user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
            self.logger.info(f"使用固定User-Agent: {user_agent}")
            
            options = webdriver.ChromeOptions()
            options.add_argument(f'user-agent={user_agent}')
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            # 在无头环境中运行时添加这些选项
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            
            # 添加插件
            options.add_argument(f'--load-extension={self.turnstile_path}')
            
            # 尝试自动查找浏览器路径
            if not browser_path:
                # 尝试常见的Chrome/Chromium位置
                possible_paths = [
                    '/usr/bin/google-chrome',
                    '/usr/bin/chromium-browser',
                    '/usr/bin/chromium',
                    '/snap/bin/chromium',
                    '/usr/lib/chromium-browser/chromium-browser'
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        browser_path = path
                        self.logger.info(f"自动找到浏览器路径: {browser_path}")
                        break
            
            if browser_path:
                options.binary_location = browser_path
                self.browser = webdriver.Chrome(options=options)
                self.logger.info("浏览器初始化成功")
            else:
                self.logger.error("浏览器初始化失败: 无法找到浏览器可执行文件路径，请手动配置。")
                self.logger.info("可通过设置环境变量BROWSER_PATH来指定浏览器路径")
                self.browser = None
            
        except Exception as e:
            self.logger.error(f"浏览器初始化失败: {str(e)}")
            self.browser = None

    def register_account(self):
        """注册Cursor账号"""
        max_retry = int(os.environ.get('MAX_RETRY', 3))
        
        for attempt in range(max_retry):
            try:
                # 首先检查浏览器是否成功初始化
                if self.browser is None:
                    self.logger.error("浏览器未初始化，无法继续注册过程")
                    break
                    
                # ... 原有的注册逻辑 ...
                
            except Exception as e:
                self.logger.info(f"当前尝试发生错误: {str(e)}")
                time.sleep(int(os.environ.get('REGISTER_INTERVAL', 2)))
                
        if attempt >= max_retry - 1:
            self.logger.info(f"达到最大重试次数 {max_retry}，注册失败")
