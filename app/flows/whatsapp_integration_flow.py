import os
import asyncio
from app.models.user import User
from app.services.flow_repository import FlowRepository
from app.schemas.user import UserBase
from app.services.letta_service import get_onboarding_agent_id, send_user_message_to_agent
from app.services.user_service import UserRepository
from app.services.whatsapp_service import WhatsAppService

class WhatsappIntegrationFlow:
    FLOW_NAME = "whatsapp_integration"

    def __init__(self, user_id: str, data: dict = None):
        self.steps = [self.step_one, self.step_two, self.step_three, self.step_four]
        self.data = data or {}
        self.current_step = 0
        self.is_running = False
        self.flow_completed = None
        self.user_id = user_id
        self.flow_repo = FlowRepository()
        
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
            # Se não houver estado salvo, inicialize um novo
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
        wpp = WhatsAppService(session_name="principal", token=os.getenv("PRINCIPAL_WPP_SESSION_TOKEN"))
        wpp.send_message(user.phone, "Você cancelou a integração com o Whatsapp.")
        send_user_message_to_agent(onboarding_agent_id, "O usuário cancelou a integração com o Whatsapp. Pergunte a ele se deseja tentar novamente.")
        #wpp.send_message(user.phone, agent_msg)
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
            wpp = WhatsAppService(session_name="principal", token=os.getenv("PRINCIPAL_WPP_SESSION_TOKEN"))
            wpp.send_message(user.phone, "Comando inválido. Use 'iniciar', 'continuar', 'cancelar' ou 'reiniciar'.")
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
        
        wpp = WhatsAppService(session_name="principal", token=os.getenv("PRINCIPAL_WPP_SESSION_TOKEN"))
        wpp.send_message(
            user.phone, 
            f"{user_first_name}, para integrarmos o seu Whatsapp com o nosso sistema, será preciso logar em uma sessão do Whatsapp Web, siga atentamente as instruções abaixo:\n\n1. Abra essa conversa em *outro* dispositivo.\n2. Abra o Whatsapp no seu *celular*.\n3. Vá até as configurações do Whatsapp e clique em *Dispositivos Conectados*.\n4. Aponte a câmera do seu celular para o *QR Code* que será exibido nessa conversa.\n5. Aguarde a confirmação da integração."
        )
        wpp.send_message(
            user.phone, 
            f"Para prosseguir, responda 'ok' ou 'continuar'."
        )
        
        await asyncio.sleep(1)
        auto_continue = False
        message = f"Step 1 completed: Explanation message sent to {user.name}"
        return {"message": message, "auto_continue": auto_continue}

    async def step_two(self):
        user = await self.get_user()

        user_repo = UserRepository()
        user_session = f"info_agent_{user.phone}"
        user_wpp = WhatsAppService(session_name=user_session)
        whatsapp_token = user_wpp.generate_token()
        user_update = UserBase(id_session_wpp=user_session, token_wpp=whatsapp_token)
        await user_repo.update_user_by_id(user.id, user_update)
        
        wpp = WhatsAppService(session_name="principal", token=os.getenv("PRINCIPAL_WPP_SESSION_TOKEN"))
        wpp.send_message(
            user.phone, 
            f"Na próxima etapa, *você deve ser rápido*, uma vez que o código QR gerado, *expira* em segundos, por favor, garanta que já consegue escanear o código com seu celular, antes de prosseguir.\n\nPara prosseguir, responda 'ok' ou 'continuar'."
        )
        
        await asyncio.sleep(1)  
        auto_continue = False
        message = f"Step 2 completed: Session ID has been defined and saved to user {user.name}. Token has been generated and saved to user {user.name}"
        return {"message": message, "auto_continue": auto_continue}

    async def step_three(self):
        user = await self.get_user()
        wpp = WhatsAppService(session_name="principal", token=os.getenv("PRINCIPAL_WPP_SESSION_TOKEN"))
        wpp.send_message(user.phone, "Aguarde um momento, estou gerando o QR Code para você.")
        user_wpp = WhatsAppService(session_name=user.id_session_wpp, token=user.token_wpp)
        response = user_wpp.start_session()
        await asyncio.sleep(3)
        attempt = 0
        while response.get("status") != "QRCODE" and attempt < 10:
            await asyncio.sleep(2)
            response = user_wpp.start_session()
            attempt += 1
        if response.get("status") == "QRCODE":
            qr_code = response.get("qrcode")
        else:
            print("Error getting QR Code")
        
        try:
            wpp = WhatsAppService(session_name="principal", token=os.getenv("PRINCIPAL_WPP_SESSION_TOKEN"))
            wpp.send_image(phone=user.phone, base64_str=qr_code, caption="Escaneie o QR Code para prosseguir com a integração.", filename="qr_code.png")
        except Exception as e:
            print(f"Error sending QR Code image: {str(e)}")
            raise
        
        await asyncio.sleep(1)
        auto_continue = True
        message = f"Step 3 completed: QR-Code was sent for user {user.name}"
        return {"message": message, "auto_continue": auto_continue}

    async def step_four(self):
        user = await self.get_user()
        user_wpp = WhatsAppService(session_name=user.id_session_wpp, token=user.token_wpp)
        user_repo = UserRepository()
        wpp = WhatsAppService(session_name="principal", token=os.getenv("PRINCIPAL_WPP_SESSION_TOKEN"))
        attempt = 0
        status = None
        onboarding_agent_id = get_onboarding_agent_id(user.phone)
        while attempt < 15 and status != "Connected":
            await asyncio.sleep(2)
            status = user_wpp.status_session().get("message")
            attempt += 1
        
        if status == "Connected":
            wpp.send_message(user.phone, "Sua integração foi realizada com sucesso! ✅")
            user_update = UserBase(whatsapp_integration=True)
            await user_repo.update_user_by_id(user.id, user_update)
            send_user_message_to_agent(onboarding_agent_id, "Integração do Whatsapp realizada com sucesso!")
            #wpp.send_message(user.phone, agent_msg)
            message = f"Step 4 completed: Integration completed for user {user.name}"
        else:
            wpp.send_message(user.phone, "Algo deu errado na sua integração, tente novamente solicitando ao agente! ❌")
            send_user_message_to_agent(onboarding_agent_id, "Integração do Whatsapp falhou!. Você deve perguntar ao usuário se ele quer tentar novamente.")
            #wpp.send_message(user.phone, agent_msg)
            message = f"Step 4 completed: Something went wrong and the integration is not completed for user {user.name}"
        
        user_update = UserBase(integration_is_running=None)
        await user_repo.update_user_by_id(user.id, user_update)
        
        await asyncio.sleep(1)
        auto_continue = True
        return {"message": message, "auto_continue": auto_continue}
