from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    name: Optional[str] = Field(None, max_length=50, description="Nome do usuário")
    phone: Optional[str] = Field(None, max_length=15, description="Telefone do usuário")  # Limite de 15 caracteres
    is_active: bool = Field(default=True, description="Indica se o usuário está ativo")
    cpf: Optional[str] = Field(None, pattern=r'^\d{11}$', description="CPF com 11 dígitos")  # CPF validado por regex
    integration_is_running: Optional[str] = Field(None, description="Indica se uma integração está em execução")
    id_main_agent: Optional[str] = Field(None, description="Identificador do agente principal")
    id_session_wpp: Optional[str] = Field(None, description="Identificador da sessão do WhatsApp")
    token_wpp: Optional[str] = Field(None, max_length=255, description="Token do WhatsApp")
    whatsapp_integration: Optional[bool] = Field(False, description="Indica integração com o WhatsApp")
    google_calendar_integration: Optional[bool] = Field(False, description="Indica integração com o Google Calendar")
    apple_calendar_integration: Optional[bool] = Field(False, description="Indica integração com o Apple Calendar")
    email_integration: Optional[bool] = Field(False, description="Indica integração com o Email")


class UserCreate(UserBase):
    """Esquema para criação de um usuário."""
    pass  # Nenhum campo extra necessário para criação


class UserResponse(UserBase):
    id: str = Field(..., description="UUID do usuário")
    created_at: datetime = Field(..., description="Data de criação do usuário")

    class Config:
        from_attributes = True
