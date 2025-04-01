# Cursor Auto Register 本地开发指南

本项目是建在巨人肩膀上的一个开源项目，Fork自cursor-auto-register项目基础上添加支持自定义域名通过cf转发Gmail邮箱等功能，为本地开发，不做收费，仅供学习参考。
参考项目：

- [chengazhen/cursor-auto-free](https://github.com/chengazhen/cursor-auto-free)：Cursor Pro 自动化工具

- [cursor-account-api](https://github.com/Elawen-Carl/cursor-account-api)：Cursor Account API

- [cursor-auto-register](https://github.com/Elawen-Carl/cursor-auto-register)：Cursor Auto Register

## 环境要求
- Python 3.10+
- pip (Python包管理器)

## 本地开发设置步骤

1. 安装 Python 依赖
```bash
pip install -r requirements.txt
```

2. 配置环境变量
- 按照 `.env.example` 配置 `.env` 环境参数
```bash
cp .env.example .env
```

## 使用说明

### 1. 环境变量配置：
在项目根目录创建 .env 文件：
```
# 多个域名使用逗号分隔
EMAIL_DOMAINS=xxx.xx

# 临时邮箱用户名
EMAIL_USERNAME=test
# 临时邮箱PIN码（如果需要）
EMAIL_PIN=

# 数据库URL
DATABASE_URL="sqlite+aiosqlite:///./accounts.db"

# ===== API服务配置 =====
# API服务监听主机地址，0.0.0.0 允许非本机访问
API_HOST="0.0.0.0"
# API服务端口号
API_PORT=8000
# 是否启用UI
ENABLE_UI=True
# 最大注册账号数量
MAX_ACCOUNTS=1

# windows用户部分安装时是自定义目录安装的，需要修改该配置
#CURSOR_PATH="D:\devtools\cursor"
```
### 参数特殊说明：

- EMAIL_DOMAINS：自己申请的邮箱，并已将DNS解析到cloudflare上了

- EMAIL_USERNAME： https://tempmail.plus/ 获取到的邮箱前缀，示例：ddcat

  需要 cloudflare 上配置转发，可以参考：https://blog.csdn.net/qq_50082325/article/details/144530594 

  把 Catch-all地址 都转发到 tempmail.plus 获取到的邮箱即可

  ![3](./images/3.jpg)



### 3. 数据持久化：

数据库文件会保存在 `accounts.db` 文件
日志文件会保存在容器内的 `api.log`
*注意事项：*
确保 `.env` 文件中的配置正确
数据目录 `accounts.db`需要适当的权限
容器内使用无头模式运行Chrome浏览器
API服务默认在8000端口运行

### 检查API服务是否正常运行
```
curl http://localhost:8000/health
```

## API 端点

- `GET /accounts` - 获取所有账号
- `GET /account/random` - 随机获取一个账号
- `POST /account` - 创建新账号

## 可视化页面
运行服务器后，访问：
- UI: http://localhost:8000/

  ![首页](./images/1.jpg)

  ![配置](./images/4.jpg)

  ![使用](./images/2.jpg)

## API 文档
运行服务器后，访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 开发工具建议
- Cursor 或 PyCharm

## 调试提示
1. 查看日志
```bash
tail -f app.log
```

## 最近更新

### 功能改进

1. **实时注册进度显示**
   - 全新优化的进度显示界面，更直观展示注册流程各阶段
   - 基于任务时间点的精确日志过滤，避免错误解析历史日志
   - 进度条精确显示从0%-100%的完整注册过程

2. **日志分析系统**
   - 智能解析日志识别注册各阶段进度
   - 防止进度回退机制，确保进度条平滑前进
   - 支持提取并显示验证码信息

3. **稳定性优化**
   - 修复"code变量引用错误"等问题
   - 改进错误处理和异常捕获
   - 日志保存系统优化，减少文件IO

### 使用提示

- 点击"注册新账号"按钮后，系统会实时显示注册进度
- 进度条将展示从准备开始(0%)到注册完成(100%)的全过程
- 可随时查看"任务控制"面板了解系统状态

## 免责声明

本扩展仅供学习和测试使用. 使用本扩展可能违反 Cursor 的服务条款,
请自行承担使用风险.

您可以:

- ✅ 复制、分发本项目
- ✅ 修改、演绎本项目
- ✅ 私人使用

但必须遵循以下规则:

- 📝 署名 - 标明原作者及修改情况
- 🚫 非商业性使用 - 不得用于商业目的
- 🔄 相同方式共享 - 修改后的作品需使用相同的协议