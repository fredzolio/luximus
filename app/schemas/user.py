from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None)  # Sem validação de formato
    cpf: Optional[str] = Field(None, pattern=r'^\d{11}$')  # CPF com 11 dígitos


class UserCreate(UserBase):
    """Esquema para criação de um usuário."""
    pass  # Nenhum campo extra necessário para criação


class UserResponse(UserBase):
    id: str = Field(..., description="UUID do usuário")
    is_active: bool = True
    created_at: datetime
    id_main_agent: Optional[str] = Field(None, description="Identificador do agente principal")
    id_session_wpp: Optional[str] = Field(None, description="Identificador da sessão do WhatsApp")

    class Config:
        from_attributes = True
