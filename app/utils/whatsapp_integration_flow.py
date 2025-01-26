from dotenv import load_dotenv
import os
from app.services.whatsapp_service import WhatsAppService
import asyncio

load_dotenv()
token = os.getenv("PRINCIPAL_WPP_SESSION_TOKEN")
wpp = WhatsAppService(session_name="principal", token=token)

# 1º passo: Enviar mensagem de explicação para o usuário.
async def step_one(data):
    user = data['user']
    user_first_name = user.name.split()[0]
    wpp.send_message(
      user.phone, 
      f"{user_first_name}, para integrarmos o seu Whatsapp com o nosso sistema, será preciso logar em uma sessão do Whatsapp Web, siga atentamente as instruções abaixo:\n\n1. Abra essa conversa em *outro* dispositivo.\n2. Abra o Whatsapp no seu *celular*.\n2. Vá até as configurações do Whatsapp e clique em *Dispositivos Conectados*.\n3. Aponte a câmera do seu celular para o *QR Code* que será exibido nessa conversa.\n4. Aguarde a confirmação da integração."
      )
    await asyncio.sleep(1)
    auto_continue = True
    message = f"Step 1 completed"
    return {"message": message, "auto_continue": auto_continue}

async def step_two(data):
    exemple = data['example']
    
    await asyncio.sleep(1)  
    auto_continue = True
    message = f"Step 2 completed"
    return {"message": message, "auto_continue": auto_continue}

async def step_three(data):
    user = data['user']
    task = data['task']
    await asyncio.sleep(1)  # Substitua por uma operação real
    auto_continue = True
    message = f"Step 3 completed for user: {user}, task: {task}"
    return {"message": message, "auto_continue": auto_continue}

class WhatsappIntegrationFlow:
    def __init__(self, data=None):
        self.steps = [step_one, step_two, step_three]
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

# async def step_two(data):
#     exemple = data['example']
    
#     await asyncio.sleep(1)  
#     auto_continue = True
#     message = f"Step 2 completed"
#     return {"message": message, "auto_continue": auto_continue}