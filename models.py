from sqlalchemy import Column, Integer, String, Boolean, Enum, Text, DateTime
from datetime import datetime
from database import Base
import enum

class MemberStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"

class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, unique=True, index=True)
    password = Column(String)
    name = Column(String)
    club = Column(String)
    status = Column(Enum(MemberStatus), default=MemberStatus.active)
    role = Column(String, default="member")  # 'admin' 또는 'member'

class Notice(Base):
    __tablename__ = "site_notice"
    id = Column(Integer, primary_key=True)
    content = Column(Text, default="")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True)
    student_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    club = Column(String, default="")
    role = Column(String, default="member")
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
