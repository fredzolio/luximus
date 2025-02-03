import os
import asyncio
import json
from typing import Optional
from urllib.parse import urlencode
from app.models.user import User
from app.services.flow_repository import FlowRepository
from app.schemas.user import UserBase
from app.services.letta_service import get_onboarding_agent_id, send_user_message_to_agent
from app.services.short_links import create_short_url
from app.services.user_service import UserRepository
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.services.whatsapp_service import WhatsAppService
from app.utils.state_utils_jwt import generate_state

class GoogleIntegrationFlow:
    FLOW_NAME = "google_integration"

    def __init__(self, user_id: str, data: dict = None):
        self.steps = [
            self.step_one,
            self.step_two,
            self.step_three,
            self.step_four
        ]
        self.data = data or {}
        self.current_step = 0
        self.is_running = False
        self.flow_completed = None
        self.user_id = user_id
        self.flow_repo = FlowRepository()
        self.wpp = WhatsAppService(session_name="principal", token=os.getenv("PRINCIPAL_WPP_SESSION_TOKEN"))

    async def get_user(self) -> User:
        user_repo = UserRepository()
        user = await user_repo.get_user_by_id(self.user_id)
        if not user:
            raise ValueError(f"User with ID {self.user_id} not found.")
        return user

    async def load_state(self):
        flow_state = await self.flow_repo.get_flow_state(self.FLOW_NAME, self.user_id)
        if flow_state:
            self.current_step = flow_state.get("current_step", 0)
            self.is_running = flow_state.get("is_running", False)
            self.flow_completed = flow_state.get("flow_completed", None)
            self.data = flow_state.get("data", {})
        else:
            await self.save_state()

    async def save_state(self):
        state = {
            "current_step": self.current_step,
            "is_running": self.is_running,
            "flow_completed": self.flow_completed,
            "data": self.data
        }
        await self.flow_repo.set_flow_state(self.FLOW_NAME, self.user_id, state)

    async def start(self, data: dict = None):
        if self.is_running:
            current_step_result = await self.execute_current_step()
            await self.save_state()
            return {
                "message": "Flow is already running.",
                "current_step": current_step_result["message"],
            }
        self.data = data or self.data
        self.current_step = 0
        self.is_running = True
        self.flow_completed = False
        await self.save_state()
        return await self.advance_flow()

    async def advance_flow(self):
        try:
            if self.current_step >= len(self.steps):
                self.is_running = False
                self.flow_completed = True
                await self.save_state()
                await self.flow_repo.delete_flow_state(self.FLOW_NAME, self.user_id)
                return {"message": "Flow completed successfully"}

            current_step_func = self.steps[self.current_step]
            step_result = await current_step_func()
            response = {"message": step_result["message"]}

            if step_result.get("auto_continue"):
                self.current_step += 1
                await self.save_state()
                next_response = await self.advance_flow()
                response["message"] += " " + next_response["message"]
            else:
                response["current_step"] = self.current_step
                self.current_step += 1
                await self.save_state()
            return response
        except Exception as e:
            self.is_running = False
            self.flow_completed = False
            await self.save_state()
            return {"error": f"An error occurred: {str(e)}"}

    async def continue_flow(self):
        if not self.is_running:
            return {"error": "Flow is not running."}
        if self.current_step is None:
            return {"error": "Flow has not been started."}
        return await self.advance_flow()

    async def stop(self):
        if not self.is_running:
            return {"error": "Flow is not running."}
        self.is_running = False
        self.flow_completed = False
        await self.save_state()
        user = await self.get_user()
        onboarding_agent_id = get_onboarding_agent_id(user.phone)
        self.wpp.send_message(user.phone, "```Você cancelou a integração com o Google Calendar.```")
        send_user_message_to_agent(onboarding_agent_id, "SYSTEM MESSAGE: O usuário cancelou a integração com o Google Calendar. Pergunte a ele se deseja tentar novamente.")
        user_repo = UserRepository()
        await user_repo.set_user_integration_running(user.phone, None)
        return {"message": "Flow stopped"}

    async def restart(self, data: dict = None):
        self.data = data or self.data
        self.current_step = 0
        self.is_running = True
        self.flow_completed = False
        await self.save_state()
        return await self.advance_flow()

    async def handle_message(self, msg: str):
        msg = msg.lower()
        if msg in ["start", "iniciar"]:
            return await self.start()
        elif msg in ["continue", "ok", "continuar"]:
            return await self.continue_flow()
        elif msg in ["stop", "cancel", "cancelar"]:
            return await self.stop()
        elif msg in ["restart", "reiniciar"]:
            return await self.restart()
        else:
            user = await self.get_user()
            self.wpp.send_message(user.phone, "```Comando inválido. Use 'iniciar', 'continuar', 'cancelar' ou 'reiniciar'.```")
            return {"error": "Invalid command. Use 'start', 'continue', 'stop', or 'restart'."}

    async def execute_current_step(self):
        if self.current_step >= len(self.steps):
            return {"message": "No more steps to execute."}
        current_step_func = self.steps[self.current_step]
        return await current_step_func()

    ####################################################################################################

    async def step_one(self):
        user = await self.get_user()
        user_first_name = user.name.split()[0]
        
        self.wpp.send_message(
            user.phone, 
            f"*{user_first_name}*, estamos iniciando a integração com sua conta do Google, enquanto geramos o link de autorização, por favor aguarde um momento."
        )
        
        state = generate_state(user_id=user.id)
        authorization_url = self.get_authorization_url(state)
        shorted_link = create_short_url(authorization_url) 

        self.wpp.send_message(
            user.phone, 
            f"*{user_first_name}*, para integrarmos o Google, preciso que você autorize o acesso. Clique no link abaixo para continuar:\n\n{shorted_link}\n\nApós autorizar, volte aqui e aguarde a confirmação."
        )

        await asyncio.sleep(1)
        auto_continue = False
        message = "Step 1 completed: Authorization link sent to the user."
        return {"message": message, "auto_continue": auto_continue}

    async def step_two(self):
        await self.load_state()
        tokens = self.data.get("tokens")
        if not tokens:
            message = "Aguardando o usuário autorizar o acesso ao Google Calendar."
            return {"message": message, "auto_continue": True}

        # Validar os tokens
        credentials = Credentials(
            tokens["token"],
            refresh_token=tokens.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        )

        if not credentials.valid:
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                # Atualizar tokens no estado
                self.data["tokens"]["token"] = credentials.token
                await self.save_state()
            else:
                raise ValueError("Credenciais inválidas e não podem ser atualizadas.")

        self.data["credentials"] = credentials.to_json()
        await self.save_state()

        message = "Step 2 completed: Authorization successful."
        return {"message": message, "auto_continue": True}

    async def step_three(self):
        user = await self.get_user()
        # Passo 3: Confirmar a integração e armazenar credenciais
        credentials_json = self.data.get("credentials")
        if not credentials_json:
            message = "Credenciais não encontradas. Recomeçando o fluxo."
            self.wpp.send_message(user.phone, "```Credenciais não encontradas. Recomeçando o fluxo.```")
            self.restart()
            return {"message": message, "auto_continue": False}

        credentials = Credentials.from_authorized_user_info(json.loads(credentials_json))
        user_repo = UserRepository()
        onboarding_agent_id = get_onboarding_agent_id(user.phone)
        # Aqui, você pode construir o serviço Calendar para verificar se está funcionando
        try:
            build('calendar', 'v3', credentials=credentials)
            self.wpp.send_message(user.phone, "```Sua integração foi realizada com sucesso!``` ✅")
            user_update = UserBase(google_calendar_integration=True, email_integration=True, apple_calendar_integration=True)
            await user_repo.update_user_by_id(user.id, user_update)
            send_user_message_to_agent(onboarding_agent_id, "SYSTEM MESSAGE: Integração do Google realizada com sucesso!")
        except Exception as e:
            self.wpp.send_message(user.phone, "```Algo deu errado na sua integração com o Google.``` ❌")
            send_user_message_to_agent(onboarding_agent_id, "SYSTEM MESSAGE: Integração do Google falhou!. Você deve perguntar ao usuário se ele quer tentar novamente.")
            self.stop()

        message = f"Step 3 completed: Google Calendar confirmado e integrado."
        return {"message": message, "auto_continue": True}

    async def step_four(self):
        user = await self.get_user()
        user_repo = UserRepository()
        user_update = UserBase(integration_is_running=None)
        await user_repo.update_user_by_id(user.id, user_update)
        self.is_running = False
        self.flow_completed = True
        await self.save_state()
        return {"message": "Google Calendar integration completed successfully!", "auto_continue": True}

    ####################################################################################################

    def get_authorization_url(self, state: str) -> str:
        # Configurar o fluxo de OAuth 2.0
        scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/gmail.compose',
            'https://www.googleapis.com/auth/gmail.readonly'
        ]
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=scopes,
            redirect_uri=os.getenv("OAUTH_REDIRECT_URI")
        )

        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=state
        )

        return authorization_url
