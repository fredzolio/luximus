import os
import re
import logging
from dotenv import load_dotenv
from httpx import Client
from letta_client import Letta, MessageCreate, AssistantMessage

from app.services.user_service import UserRepository
from app.services.whatsapp_service import WhatsAppService

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar o cliente HTTPX personalizado
custom_httpx_client = Client(headers={"x-bare-password": os.getenv("LETTA_AI_API_PASSWORD")})

# Inicializar o cliente Letta
lc = Letta(
    base_url=os.getenv("LETTA_AI_API_URL"),
    httpx_client=custom_httpx_client,
)

# Inicializar repositórios e serviços
user_repo = UserRepository()

wpp = WhatsAppService(session_name="principal", token=os.getenv("PRINCIPAL_WPP_SESSION_TOKEN"))

def get_phone_tag(agent_id: str) -> str:
    """
    Recupera o número de telefone associado a um agente com base nas tags.
    """
    try:
        agent = lc.agents.retrieve(agent_id)
        tags = agent.tags
        for tag in tags:
            if re.search(r'\d+', tag):
                return tag
    except Exception as e:
        logging.error(f"Erro ao recuperar agente {agent_id}: {e}")
    return ""
