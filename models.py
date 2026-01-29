from sqlalchemy import Column, Integer, String, Boolean, Enum
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