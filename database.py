from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Text, text, BigInteger, ForeignKey
from contextlib import asynccontextmanager
from logger import info, error
from config import DATABASE_URL


# 基础模型类
class Base(DeclarativeBase):
    pass


# 账号模型
class AccountModel(Base):
    __tablename__ = "accounts"
    email = Column(String, primary_key=True)
    user = Column(String, nullable=False)
    password = Column(String, nullable=True)
    token = Column(String, nullable=False)
    usage_limit = Column(Text, nullable=True)
    created_at = Column(Text, nullable=True)
    status = Column(String, default="active", nullable=False)
    id = Column(BigInteger, nullable=False, index=True)  # 添加毫秒时间戳列并创建索引


# 账号使用记录模型
class AccountUsageRecordModel(Base):
    __tablename__ = "account_usage_records"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    account_id = Column(BigInteger, nullable=False, index=True)  # 账号ID
    email = Column(String, nullable=False, index=True)  # 账号邮箱
    ip = Column(String, nullable=True)  # 使用者IP
    user_agent = Column(Text, nullable=True)  # 使用者UA
    created_at = Column(Text, nullable=False)  # 创建时间


def create_engine():
    """创建数据库引擎"""
    # 直接使用配置文件中的数据库URL
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
        future=True,
    )
    # info(f"数据库引擎创建成功: {DATABASE_URL}")
    return engine


@asynccontextmanager
async def get_session() -> AsyncSession:
    """创建数据库会话的异步上下文管理器"""
    # 为每个请求创建新的引擎和会话
    engine = create_engine()
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, future=True
    )

    session = async_session()
    try:
        # 确保连接有效
        await session.execute(text("SELECT 1"))
        yield session
    except Exception as e:
        error(f"数据库会话错误: {str(e)}")
        try:
            await session.rollback()
        except Exception as rollback_error:
            error(f"回滚过程中出错: {str(rollback_error)}")
        raise
    finally:
        try:
            await session.close()
        except Exception as e:
            error(f"关闭会话时出错: {str(e)}")
        try:
            await engine.dispose()
        except Exception as e:
            error(f"释放引擎时出错: {str(e)}")


async def init_db():
    """初始化数据库表结构"""
    try:
        engine = create_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()
        info("数据库初始化成功")
    except Exception as e:
        error(f"数据库初始化失败: {str(e)}")
        raise
