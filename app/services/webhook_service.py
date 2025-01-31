import asyncio
import os
from app.flows.create_agents_flow import CreateAgentsFlow
from app.flows.google_integration_flow import GoogleIntegrationFlow
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user_service import UserRepository
from app.services.whatsapp_service import WhatsAppService
from app.flows.whatsapp_integration_flow import WhatsappIntegrationFlow
from app.utils.archival_memory_manager import background_agent_archival_memory_insert
from .letta_service import send_user_message_to_agent, get_onboarding_agent_id
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("PRINCIPAL_WPP_SESSION_TOKEN")
wpp = WhatsAppService(session_name="principal", token=token)

class WebhookService:
    @staticmethod
    async def process_onmessage_event(payload: dict):
        user_name = payload.get("notifyName")
        user_number = payload["sender"]["id"].replace("@c.us", "")
        message = payload.get("body")
        session = payload.get("session")
        msg_type = payload.get("type")
        is_group = payload.get("isGroupMsg")
        group_id = payload.get("from")
        
        if msg_type != "chat":
            return {"status": "ignored", "message": "Evento não processado."}

        try:
            if session == "principal":
                user = await WebhookService.get_or_create_user_if_not_exists(user_number, user_name)

                integration_status = user.integration_is_running
                if integration_status is None:
                    WebhookService.perform_action_based_on_message(message, user)
                elif integration_status == "whatsapp":
                    flow = WhatsappIntegrationFlow(user.id)
                    await flow.load_state()
                    await flow.handle_message(message)
                elif integration_status == "google_calendar":
                    flow = GoogleIntegrationFlow(user.id)
                    await flow.load_state()
                    await flow.handle_message(message)
                else:
                    pass
            else:
                await background_agent_archival_memory_insert(
                    session=session,
                    message=message,
                    origem="WhatsApp",
                    phone=user_number,
                    name=user_name,
                    is_group=is_group,
                    group_id=group_id
                )

            return {
                "user_name": user_name,
                "user_number": user_number,
                "message": message,
                "session": session
            }

        except Exception as e:
            print(f"Erro ao processar evento de mensagem (User: {user_name}, Number: {user_number}): {e}")
            raise e


    @staticmethod
    async def get_or_create_user_if_not_exists(user_number: str, user_name: str):
        user_repo = UserRepository()
        try:
            user = await user_repo.get_user_by_phone(phone=user_number)
            
            if user:
                return user

            wpp.send_message(
                user_number, 
                f"Olá, *{user_name}*.\n\nComo é sua primeira vez por aqui, irei criar o seu perfil no sistema, *aguarde um momento*."
            )
            new_user = await user_repo.create_user(user=UserCreate(name=user_name, phone=user_number))
            
            agents_flow = CreateAgentsFlow(new_user.id)
            await agents_flow.load_state()
            await agents_flow.restart()
            return new_user

        except Exception as e:
            print(f"Erro ao criar ou buscar usuário (Número: {user_number}, Nome: {user_name}): {e}")
            raise e


    @staticmethod
    def perform_action_based_on_message(message: str, user: User):
        is_user_fully_integrated = all([
            user.id_main_agent,
            user.whatsapp_integration,
            user.apple_calendar_integration,
            user.google_calendar_integration,
            user.email_integration
        ])

        agent_id = (
            user.id_main_agent if is_user_fully_integrated
            else get_onboarding_agent_id(user.phone)
        )
        
        send_user_message_to_agent(agent_id, message)

