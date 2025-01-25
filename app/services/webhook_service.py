import os
from letta_client import MessageCreate
from app.agents.main_agent import create_main_agent
from app.models.user import User
from app.schemas.user import UserBase, UserCreate
from app.services.user_service import UserRepository
from app.services.whatsapp_service import WhatsAppService
from app.agents.onboarding_agent import create_onboarding_agent
from .letta_service import get_human_block_id, send_user_message_to_agent, get_onboarding_agent_id
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("PRINCIPAL_WPP_SESSION_TOKEN")
wpp = WhatsAppService(session_name="principal", token=token)

class WebhookService:
    
    
    @staticmethod
    async def process_onmessage_event(payload: dict):
        user_name = payload.get('notifyName')
        user_number = payload.get('from').replace("@c.us", "")
        message = payload.get('body')
        session = payload.get('session')
        
        if session == "principal":
            user = await WebhookService.create_user_if_not_exists(user_number, user_name)
            WebhookService.perform_action_based_on_message(message, user)
        # else:
        #     send_message_to_background_agent(user_name, user_number, message, session)

        return {
            "user_name": user_name,
            "user_number": user_number,
            "message": message,
            "session": session
        }

    @staticmethod
    async def create_user_if_not_exists(user_number: str, user_name: str):
        user_repo = UserRepository()
        try:
            user = await user_repo.get_user_by_phone(phone=user_number)
            if not user:
                wpp.send_message(user_number, f"Olá, *{user_name}*.\n\nComo é sua primeira vez por aqui, irei criar o seu perfil no sistema, *aguarde um momento*.")
                new_user = await user_repo.create_user(user=UserCreate(name=user_name, phone=user_number))
                onboarding_agent = create_onboarding_agent(user_name=new_user.name, user_number=new_user.phone)
                human_block_id = get_human_block_id(onboarding_agent.id)
                main_agent = create_main_agent(user_name=new_user.name, user_number=new_user.phone, human_block_id=human_block_id)
                user_main_agent_id_update = UserBase(id_main_agent=main_agent.id)
                await user_repo.update_user_by_id(new_user.id, user_main_agent_id_update)
                return new_user
            else:
                return user
        except Exception as e:
            print(f"Erro ao criar ou buscar usuário: {e}")

    @staticmethod
    def perform_action_based_on_message(message: str, user: User):
        if user.id_main_agent is None or not user.whatsapp_integration or not user.apple_calendar_integration or not user.google_calendar_integration or not user.email_integration:
            agent_id = get_onboarding_agent_id(user.phone)
            agent_response = send_user_message_to_agent(agent_id, message)
        else:
            agent_response = send_user_message_to_agent(user.id_main_agent, message)
        wpp.send_message(user.phone, agent_response)
