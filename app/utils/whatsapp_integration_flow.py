from dotenv import load_dotenv
import os
from app.schemas.user import UserBase
from app.services.user_service import UserRepository
from app.services.whatsapp_service import WhatsAppService
import asyncio

load_dotenv()
token = os.getenv("PRINCIPAL_WPP_SESSION_TOKEN")
wpp = WhatsAppService(session_name="principal", token=token)

############################################################################################################################################################################

async def step_one(data):
    user = data['user']
    user_first_name = user.name.split()[0]
    
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

async def step_two(data):
    user = data['user']
    
    user_repo = UserRepository()
    user_session = f"info_agent_{user.phone}"
    user_wpp = WhatsAppService(session_name=user_session)
    whatsapp_token = user_wpp.generate_token()
    user_update = UserBase(id_session_wpp=user_session, token_wpp=whatsapp_token)
    await user_repo.update_user_by_id(user.id, user_update)
    wpp.send_message(
        user.phone, 
        f"Na próxima etapa, *você deve ser rápido*, uma vez que o código QR gerado, *expira* em segundos, por favor, garanta que já consegue escanear o código com seu celular, antes de prosseguir.\n\nPara prosseguir, responda 'ok' ou 'continuar'."
    )
    
    await asyncio.sleep(1)  
    auto_continue = False
    message = f"Step 2 completed: Session ID has been defined and saved to user {user.name}. Token has been generated and saved to user {user.name}"
    return {"message": message, "auto_continue": auto_continue}

async def step_three(data):
    user = data['user']

    user_wpp = WhatsAppService(session_name=user.id_session_wpp, token=user.token_wpp)
    first_response = user_wpp.start_session()
    await asyncio.sleep(3)
    if first_response.get("status") == "QRCODE":
        qr_code = user_wpp.start_session().get("qrcode")
    else:
        await asyncio.sleep(2)
        qr_code = user_wpp.start_session().get("qrcode")
    wpp.send_file(user.phone, qr_code)
    
    await asyncio.sleep(1)
    auto_continue = True
    message = f"Step 3 completed: QR-Code was sended for user {user.name}"
    return {"message": message, "auto_continue": auto_continue}

async def step_four(data):
    user = data['user']
    user_wpp = WhatsAppService(session_name=user.id_session_wpp, token=user.token_wpp)
    await asyncio.sleep(4)
    status = user_wpp.status_session().get("status")
    if status:
        wpp.send_message(user.phone, "Sua integração foi realizada com sucesso! ✅")
        message = f"Step 4 completed: Integration completed for user {user.name}"
    else:
        wpp.send_message(user.phone, "Algo deu errado na sua integração, tente novamente solicitando ao agente! ❌")
        message = f"Step 4 completed: Something goes wrong and the integration is not completed for user {user.name}"
    
    await asyncio.sleep(1)
    auto_continue = True
    return {"message": message, "auto_continue": auto_continue}

############################################################################################################################################################################

class WhatsappIntegrationFlow:
    def __init__(self, data=None):
        self.steps = [step_one, step_two, step_three, step_four]
        self.data = data
        self.current_step = 0
        self.is_running = False
        self.flow_completed = None

    async def start(self, data=None):
        if self.is_running:
            current_step_result = await self.execute_current_step()
            return {
                "message": "Flow is already running.",
                "current_step": current_step_result["message"],
            }
        self.data = data or self.data
        self.current_step = 0
        self.is_running = True
        self.flow_completed = None
        return await self.advance_flow()

    async def advance_flow(self):
        try:
            if self.current_step >= len(self.steps):
                self.is_running = False
                self.flow_completed = True
                return {"message": "Flow completed successfully"}

            current_step_func = self.steps[self.current_step]
            step_result = await current_step_func(self.data)
            response = {"message": step_result["message"]}

            if step_result.get("auto_continue"):
                self.current_step += 1
                next_response = await self.advance_flow()
                response["message"] += " " + next_response["message"]
            else:
                response["current_step"] = self.current_step
                self.current_step += 1
            return response
        except Exception as e:
            self.is_running = False
            self.flow_completed = False
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
        return {"message": "Flow stopped"}

    async def restart(self, data=None):
        self.data = data or self.data
        self.current_step = 0
        self.is_running = True
        self.flow_completed = None
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
            return {"error": "Invalid command. Use 'start', 'continue', 'stop', or 'restart'."}

    async def execute_current_step(self):
        if self.current_step >= len(self.steps):
            return {"message": "No more steps to execute."}
        current_step_func = self.steps[self.current_step]
        return await current_step_func(self.data)

############################################################################################################################################################################