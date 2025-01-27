import re
import time
import logging
from app.services.letta_service import get_background_agent_id
from app.services.user_service import UserRepository
from app.utils.celery_imports import lc
import pytz
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

brazil_timezone = pytz.timezone("America/Sao_Paulo")
current_time = datetime.now(brazil_timezone)

async def background_agent_archival_memory_insert(session: str, message: str, origem: str, phone: str = None, name: str = None):
    """
    Insere uma mensagem na memória arquivística do agente.
    """
    
    user = await get_user_by_session(session)
    agent_id = get_background_agent_id(user.phone)
    
    text = f"""\
- Mensagem:         {message}
- Data:             {current_time.strftime("%d/%m/%Y %H:%M:%S")}
- Origem:           {origem}
"""

    if origem == "whatsapp":
      text += f"""\
- Contato:          {name if name else "Desconhecido"}
- Número do contato: {phone if phone else "Desconhecido"}
"""
    
    try:
        if phone != os.getenv("MAIN_WHATSAPP_NUMBER"):
          lc.agents.archival_memory.create(agent_id=agent_id, text=text)

    except Exception as e:
        logging.error(f"Erro ao enviar mensagem ao agente {agent_id}: {e}")


async def get_user_by_session(session: str):
  """
  Retorna o usuário a partir da sessão informada. 
  """
  
  numero = re.search(r'\d+', session).group()
  user_repo = UserRepository()
  user = await user_repo.get_user_by_phone(phone=numero)
  return user

  