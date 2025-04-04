import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# ===== 日志配置 =====
# 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
# 日志格式：时间戳 - 日志级别 - 消息内容
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
# 日志日期格式：年-月-日 时:分:秒
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ===== API服务配置 =====
# API服务监听主机地址
API_HOST = os.getenv("API_HOST", "127.0.0.1")
# API服务端口号
API_PORT = int(os.getenv("API_PORT", 8000))
# 是否启用调试模式
API_DEBUG = os.getenv("API_DEBUG", "false").lower() == "true"
# API服务工作进程数量（Windows下建议使用1）
API_WORKERS = int(os.getenv("API_WORKERS", 1))

# ===== 账号管理配置 =====
# 系统最大已激活的账号数量
MAX_ACCOUNTS = int(os.getenv("MAX_ACCOUNTS", 10))
# 每次注册间隔时间(秒)
REGISTRATION_INTERVAL = int(os.getenv("REGISTRATION_INTERVAL", 60))
# 注册失败时的最大重试次数
REGISTRATION_MAX_RETRIES = int(os.getenv("REGISTRATION_MAX_RETRIES", 3))
# 注册重试间隔时间(秒)
REGISTRATION_RETRY_INTERVAL = int(os.getenv("REGISTRATION_RETRY_INTERVAL", 5))

# ===== 浏览器配置 =====
# 是否以无头模式运行浏览器（不显示界面）
BROWSER_HEADLESS = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"
# 浏览器可执行文件路径（为空则使用默认路径）
BROWSER_PATH = os.getenv("BROWSER_PATH", None)
# 浏览器下载文件保存路径
BROWSER_DOWNLOAD_PATH = os.getenv("BROWSER_DOWNLOAD_PATH", None)
# 是否使用动态ua池
DYNAMIC_USERAGENT = os.getenv("DYNAMIC_USERAGENT", "false").lower() == "true"
# 浏览器User-Agent
BROWSER_USER_AGENT = os.getenv("BROWSER_USER_AGENT", None)

# ===== Cursor URL配置 =====
# Cursor登录页面URL
LOGIN_URL = "https://authenticator.cursor.sh"
# Cursor注册页面URL
SIGN_UP_URL = "https://authenticator.cursor.sh/sign-up"
# Cursor设置页面URL
SETTINGS_URL = "https://www.cursor.com/settings"

# ===== 邮箱配置 =====
# 邮箱验证码获取方式
EMAIL_CODE_TYPE = os.getenv("EMAIL_CODE_TYPE", "API")
# 邮箱类型
EMAIL_TYPE = os.getenv("EMAIL_TYPE", "tempemail")
# 临时邮箱用户名
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "xxx")
# 临时邮箱域名
EMAIL_DOMAIN = os.getenv("EMAIL_DOMAIN", "mailto.plus")
# 临时邮箱PIN码（如果需要）
EMAIL_PIN = os.getenv("EMAIL_PIN", "")
# 可用于注册的邮箱域名列表（逗号分隔）
EMAIL_DOMAINS = [
    domain.strip() for domain in os.getenv("EMAIL_DOMAINS", "xxx.xx").split(",") if domain.strip()
]
# ZMail API地址
EMAIL_API = os.getenv("EMAIL_API", "")
# 是否启用邮箱API代理
EMAIL_PROXY_ENABLED = os.getenv("EMAIL_PROXY_ENABLED", "false").lower() == "true"
# 邮箱API代理地址
EMAIL_PROXY_ADDRESS = os.getenv("EMAIL_PROXY_ADDRESS", "")
# 邮件验证码获取最大重试次数
EMAIL_VERIFICATION_RETRIES = int(os.getenv("EMAIL_VERIFICATION_RETRIES", 5))
# 邮件验证码获取重试间隔(秒)
EMAIL_VERIFICATION_WAIT = int(os.getenv("EMAIL_VERIFICATION_WAIT", 5))

# ===== 数据库配置 =====
# 数据库文件名
DB_NAME = "accounts.db"
# 根据操作系统生成适当的数据库文件路径
if os.name == "nt":  # Windows
    DB_PATH = os.path.join(os.getcwd(), DB_NAME)
    DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"
else:  # Linux/Unix
    DB_PATH = os.path.join("/app", DB_NAME)
    DATABASE_URL = f"sqlite+aiosqlite:{DB_PATH}"

# 允许通过环境变量覆盖默认的数据库URL
DATABASE_URL = os.getenv("DATABASE_URL", DATABASE_URL)

# ===== Cursor main.js 配置 =====
# Cursor 主文件路径
CURSOR_PATH = os.getenv("CURSOR_PATH", None)

# ===== 代理配置 =====
# 是否启用代理
USE_PROXY = os.getenv("USE_PROXY", "False").lower() == "true"
# 代理类型
PROXY_TYPE = os.getenv("PROXY_TYPE", "http")
# 代理服务器地址
PROXY_HOST = os.getenv("PROXY_HOST", "")
# 代理服务器端口
PROXY_PORT = os.getenv("PROXY_PORT", "")
# 代理服务器用户名
PROXY_USERNAME = os.getenv("PROXY_USERNAME", "")
# 代理服务器密码
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD", "")
# 代理服务器超时时间
PROXY_TIMEOUT = int(os.getenv("PROXY_TIMEOUT", "10"))

# Gmail相关配置
GMAIL_USERNAME = os.getenv("GMAIL_USERNAME", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

# 添加网易163邮箱的配置
NETEASE_USERNAME = os.getenv("NETEASE_USERNAME", "")
NETEASE_PASSWORD = os.getenv("NETEASE_PASSWORD", "")

# 添加调试输出
print(f"config.py 加载的EMAIL_DOMAINS: {EMAIL_DOMAINS}")
print(f"原始环境变量EMAIL_DOMAINS: {os.getenv('EMAIL_DOMAINS')}")

# 添加默认使用限制配置
TOTAL_USAGE = int(os.getenv("TOTAL_USAGE", "150"))