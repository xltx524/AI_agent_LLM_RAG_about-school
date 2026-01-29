import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON  # 导入 JSON 类型
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

# --- MySQL 数据库配置 (从 .env 文件读取) ---
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_DB_NAME = os.getenv("MYSQL_DB_NAME")

if not all([MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DB_NAME]):
    print("错误：MySQL 数据库环境变量未完全设置。请检查 .env 文件。")
    raise ValueError("MySQL database environment variables are not fully set.")

encoded_password = quote_plus(MYSQL_PASSWORD)
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{encoded_password}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB_NAME}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- User 模型：映射到您现有的 'user' 表 ---
class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    account = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)
    age = Column(Integer)
    sex = Column(Integer, nullable=False)
    phone_num = Column(String(20))
    role_id = Column(Integer)
    isValid = Column(String(4))

    sessions = relationship("Session", back_populates="user")


# --- Session 模型：新增的会话表，关联到 'user' 表 ---
class Session(Base):
    __tablename__ = "sessions"
    id = Column(String(36), primary_key=True, index=True, unique=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")


# --- Message 模型：新增的消息表 ---
class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), index=True)  # 确保 session_id 有索引
    role = Column(String(50), index=True)  # 消息发送者，例如 "user" 或 "assistant"
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.now, index=True)  # 消息发送时间也添加索引

    # --- 新增字段，用于问答记录与分析 ---
    # 针对用户提问的解决状态和管理员备注（通常关联到用户提出的问题）
    # 默认状态为 'pending' (待处理)
    status = Column(String(50), default="pending", nullable=False)
    admin_notes = Column(Text, nullable=True)  # 管理员对该问答轮次的备注

    # 针对AI回答的反馈和引用上下文（通常关联到AI的回答）
    feedback = Column(String(50), nullable=True)  # 'satisfied', 'dissatisfied'
    # 存储AI回答引用的知识库片段，可以是一个JSON字符串列表
    # MySQL 8+ 支持 JSON 类型，旧版本可以使用 TEXT 存储 JSON 字符串
    context_references = Column(JSON, nullable=True)  # 或者 Column(Text, nullable=True) 如果 MySQL 版本不支持 JSON 类型

    session = relationship("Session", back_populates="messages")


# --- 知识库条目模型 (KnowledgeEntry) ---
class KnowledgeEntry(Base):
    __tablename__ = "knowledge_entries"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True, nullable=False)
    type = Column(String(50), nullable=False)
    content = Column(Text, nullable=True)
    file_path = Column(String(255), nullable=True)
    source = Column(String(50), nullable=False)

    # ✅ 修复重点：添加了 processing_notes 字段
    processing_notes = Column(Text, nullable=True)

    status = Column(String(50), default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<KnowledgeEntry(id={self.id}, title='{self.title}', type='{self.type}', status='{self.status}', is_deleted={self.is_deleted})>"


# 用于创建所有数据库表的函数
def create_db_tables():
    print("Attempting to create database tables (sessions, messages, knowledge_entries)...")
    try:
        # 只创建尚未存在的表
        Base.metadata.create_all(bind=engine)
        print("Database tables (sessions, messages, knowledge_entries) created/checked successfully.")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        raise


# 依赖注入函数：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()