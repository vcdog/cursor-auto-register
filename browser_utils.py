from DrissionPage import ChromiumOptions, Chromium
import sys
import os
from logger import info, warning, error
from config import (
    BROWSER_USER_AGENT,
    BROWSER_PATH,
    BROWSER_HEADLESS,
    DYNAMIC_USERAGENT,
    USE_PROXY,
    PROXY_TYPE,
    PROXY_HOST,
    PROXY_PORT,
    PROXY_USERNAME,
    PROXY_PASSWORD,
    PROXY_TIMEOUT
)
import random
import time

from fake_useragent import UserAgent


def get_random_user_agent():
    ua = UserAgent()
    return ua.random

class BrowserManager:
    def __init__(self):
        self.browser = None

    def init_browser(self):
        try:
            info("正在初始化浏览器...")
            co = ChromiumOptions()

            # 如果配置了特定的浏览器路径，则使用
            if BROWSER_PATH and os.path.exists(BROWSER_PATH):
                co.set_browser_path(BROWSER_PATH)
                info(f"使用自定义浏览器路径: {BROWSER_PATH}")

            try:
                extension_path = self._get_extension_path()
                co.add_extension(extension_path)
            except FileNotFoundError as e:
                error(f"加载插件失败，警告: {e}")

            # 设置User-Agent
            if DYNAMIC_USERAGENT:
                # 随机选择一个User-Agent
                user_agent = get_random_user_agent()
                info(f"使用动态User-Agent: {user_agent}")
                co.set_user_agent(user_agent)
            elif BROWSER_USER_AGENT:
                info(f"使用固定User-Agent: {BROWSER_USER_AGENT}")
                co.set_user_agent(BROWSER_USER_AGENT)
            else:
                info("不配置User-Agent")

            co.set_pref("credentials_enable_service", False)
            co.set_argument("--hide-crash-restore-bubble")
            # 禁用自动化特征（关键参数）
            co.set_argument("--disable-blink-features=AutomationControlled")
            co.set_argument("--disable-features=AutomationControlled")
            co.set_argument("--disable-automation-extension")

            # 随机化指纹参数
            co.set_pref("webgl.vendor", "NVIDIA Corporation")
            co.set_pref(
                "webgl.renderer",
                "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)",
            )
            co.set_pref("navigator.plugins.length", 5)
            co.set_pref("navigator.hardwareConcurrency", 8)

            # 覆盖自动化特征（关键）
            co.set_pref("dom.webdriver.enabled", False)
            co.set_pref("useAutomationExtension", False)

            # 设置时区参数
            co.set_argument("--timezone=Asia/Shanghai")
            co.set_pref("timezone.override", "Asia/Shanghai")

            # 设置更真实的屏幕参数
            co.set_pref("screen.width", 1920)
            co.set_pref("screen.height", 1080)
            co.set_pref("screen.pixelDepth", 24)
            co.auto_port()

            # 生产环境使用无头模式
            co.headless(BROWSER_HEADLESS)

            # Mac 系统特殊处理
            if sys.platform == "darwin" or sys.platform == "linux":
                co.set_argument("--no-sandbox")
                co.set_argument("--disable-gpu")

            # 添加代理设置
            if USE_PROXY and PROXY_HOST and PROXY_PORT:
                proxy_string = f"{PROXY_TYPE}://"
                
                # 如果有认证信息
                if PROXY_USERNAME and PROXY_PASSWORD:
                    proxy_string += f"{PROXY_USERNAME}:{PROXY_PASSWORD}@"
                    
                proxy_string += f"{PROXY_HOST}:{PROXY_PORT}"
                
                info(f"使用代理: {PROXY_TYPE} {proxy_string}")
                co.set_argument(f'--proxy-server={proxy_string}')

            self.browser = Chromium(co)
            info("浏览器初始化成功")
        except Exception as e:
            error(f"浏览器初始化失败: {str(e)}")
        return self.browser

    def _get_extension_path(self):
        """获取插件路径"""
        root_dir = os.getcwd()
        extension_path = os.path.join(root_dir, "turnstilePatch")

        if hasattr(sys, "_MEIPASS"):
            extension_path = os.path.join(sys._MEIPASS, "turnstilePatch")

        if not os.path.exists(extension_path):
            raise FileNotFoundError(f"插件不存在: {extension_path}")
        info(f"插件路径: {extension_path}")
        return extension_path

    def quit(self):
        info("正在关闭浏览器...")
        try:
            if self.browser:
                self.browser.quit()
            info("浏览器已关闭")
        except Exception as e:
            error(f"关闭浏览器出错: {str(e)}")
