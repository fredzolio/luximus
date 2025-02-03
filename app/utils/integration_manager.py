import asyncio
import re
from app.schemas.user import UserBase
from app.services.letta_service import get_onboarding_agent_id, send_user_message_to_agent
from app.services.user_service import UserRepository


async def whatsapp_session_status_manager(session: str, status: str):
  """
  Gerencia o status da sessão do usuário.
  """
  done = False
  try:
    user = await get_user_by_session(session)
    user_repo = UserRepository()
    if status == "desconnectedMobile" and user.whatsapp_integration == True:
      await user_repo.update_user_by_id(user.id, UserBase(whatsapp_integration=False))
      onboarding_agent_id = get_onboarding_agent_id(user.phone)
      await asyncio.sleep(2)
      send_user_message_to_agent(onboarding_agent_id, "SYSTEM MESSAGE: A integração com o WhatsApp do usuário falhou, pergunte-o se ele deseja integrar novamente.")
      done = True
  except Exception as e:
    pass
  
  return done

async def get_user_by_session(session: str):
  """
  Retorna o usuário a partir da sessão informada. 
  """
  
  numero = re.search(r'\d+', session).group()
  user_repo = UserRepository()
  user = await user_repo.get_user_by_phone(phone=numero)
  return user