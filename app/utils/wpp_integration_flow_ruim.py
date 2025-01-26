from app.models.user import User
from dotenv import load_dotenv
import os

from app.services.whatsapp_service import WhatsAppService


load_dotenv()
token = os.getenv("PRINCIPAL_WPP_SESSION_TOKEN")

wpp = WhatsAppService(session_name="principal", token=token)


flow_state = {
    "current_step": None,
    "is_running": False
}

# 1º passo: Enviar mensagem de explicação para o usuário.
async def step_one(user: User):
    
    user_first_name = user.name.split()[0]
    wpp.send_message(
      user.phone, 
      f"Para integrarmos o seu Whatsapp com o nosso sistema, será preciso logar em uma sessão do Whatsapp Web, siga atentamente as instruções abaixo:\n\n1. Abra essa conversa em *outro* dispositivo.\n2. Abra o Whatsapp no seu *celular*.\n2. Vá até as configurações do Whatapp e clique em *Dispositivos Conectados*.\n3. Aponte a câmera do seu celular para o *QR Code* exibido nessa mensagem.\n4. Aguarde a confirmação da integração."
      )

# Lista de etapas do flow
steps = [step_one, step_two, step_three]

# Função central para controle do fluxo
def control_flow(msg: str):
    msg = msg.lower()
    
    if msg in ["start", "iniciar"]:
        if flow_state["is_running"]:
            return {"message": "Flow is already running.", "current_step": steps[flow_state["current_step"]]() if flow_state["current_step"] is not None else None}
        flow_state["current_step"] = 0
        flow_state["is_running"] = True
        return {"message": "Flow started", "current_step": steps[flow_state["current_step"]]()}

    elif msg in ["continue", "ok", "continuar"]:
        if not flow_state["is_running"]:
            return {"error": "Flow is not running."}
        if flow_state["current_step"] is None:
            return {"error": "Flow has not been started."}
        
        flow_state["current_step"] += 1
        if flow_state["current_step"] >= len(steps):
            flow_state["is_running"] = False
            flow_state["current_step"] = None
            return {"message": "Flow completed"}
        return {"message": "Flow continued", "current_step": steps[flow_state["current_step"]]()}

    elif msg in ["stop", "cancel", "cancelar"]:
        if not flow_state["is_running"]:
            return {"error": "Flow is not running."}
        flow_state["is_running"] = False
        flow_state["current_step"] = None
        return {"message": "Flow stopped"}

    elif msg in ["restart", "reiniciar"]:
        flow_state["current_step"] = 0
        flow_state["is_running"] = True
        return {"message": "Flow restarted", "current_step": steps[flow_state["current_step"]]()}

    else:
        return {"error": "Invalid command. Use 'start', 'continue', 'stop', or 'restart'."}
