import uuid
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.mysql import CHAR
from datetime import datetime
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String(50), nullable=True)
    phone = Column(String(15), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(), nullable=False)
    cpf = Column(String(11), unique=True, nullable=True)
    id_main_agent = Column(String(255), nullable=True) 
    id_session_wpp = Column(String(255), nullable=True)
    token_wpp = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, phone={self.phone})>"
