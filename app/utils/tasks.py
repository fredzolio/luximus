import time
import logging
from celery import shared_task
import os

from letta_client import MessageCreate, AssistantMessage, ToolCallMessage
from app.services.user_service import UserRepository
from app.utils.celery_imports import lc, get_phone_tag
from app.services.whatsapp_service import WhatsAppService
import redis
from asgiref.sync import async_to_sync

# Inicializar WhatsAppService
wpp = WhatsAppService(session_name="principal", token=os.getenv("PRINCIPAL_WPP_SESSION_TOKEN"))

# Configurar conexão com Redis usando redis-py (cliente síncrono)
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=os.getenv("REDIS_PORT", 6379),
    db=int(os.getenv("REDIS_DB", 0)),
    password=os.getenv("REDIS_PASSWORD", ""),
    decode_responses=True  # Decodifica automaticamente as respostas para strings
)

@shared_task
def send_message_task(agent_id: str, message: str):
    """
    Tarefa Celery para enviar mensagem ao agente e monitorar o status da execução.
    """
    try:
        # Enviar mensagem ao agente
        response = lc.agents.messages.create_async(
            agent_id=agent_id,
            messages=[
                MessageCreate(
                    role="user",
                    content=message,
                )
            ],
        )

        if not response.id:
            logging.error("A resposta da API não contém um 'response.id'.")
            phone = get_phone_tag(agent_id)
            if phone:
                wpp.send_message(phone, "Erro ao processar a mensagem: ID da resposta não encontrado.")
            return

        run_id = response.id
        phone = get_phone_tag(agent_id)

        # Armazenar run_id e phone no Redis
        redis_key = f"run:{run_id}"
        redis_client.set(redis_key, phone, ex=3600)  # Expira em 1 hora

        # Iniciar a verificação do status da execução
        check_run_status_task.delay(run_id, agent_id, timeout=30)

    except Exception as e:
        logging.error(f"Erro ao enviar mensagem ao agente {agent_id}: {e}")

@shared_task
def check_run_status_task(run_id: str, agent_id: str, timeout: int = 30, poll_interval: int = 1):
    """
    Tarefa Celery para verificar o status da execução e enviar a resposta ao usuário quando concluída.
    """
    user_repo = UserRepository()
    
    try:
        start_time = time.time()
        phone = redis_client.get(f"run:{run_id}")  # Recuperar phone do Redis

        if not phone:
            logging.error(f"Telefone do usuário não encontrado para run_id {run_id}.")
            return

        while True:
            run = lc.runs.retrieve_run(run_id)
            if run.status in ["completed", "failed"]:
                break
            if time.time() - start_time > timeout:
                logging.error(f"Timeout ao aguardar a execução do agente {agent_id}.")
                wpp.send_message(phone, "Erro: Tempo limite excedido ao aguardar a resposta do agente.")
                return
            time.sleep(poll_interval)

        # Obter as mensagens da execução
        messages = lc.runs.list_run_messages(run_id)
        assistant_message = next(
            (msg.content for msg in messages if isinstance(msg, AssistantMessage)),
            None
        )

        send_message = True
        
        tool_called = next(
            (msg.tool_call.name for msg in messages if isinstance(msg, ToolCallMessage)),
            None
        )
        
        if tool_called:
            flagged_tools = any([
                "start_whatsapp_integration" in tool_called
            ])
            if flagged_tools:
                send_message = False
        
        if assistant_message:
            if send_message:
                wpp.send_message(phone, assistant_message)
            else:
                pass
        else:
            logging.error(f"A resposta do agente {agent_id} não contém 'assistant_message'. Estrutura: {messages}")
            wpp.send_message(phone, "Erro: Não foi possível encontrar a mensagem do agente.")

        # Remover a chave do Redis após o envio
        redis_client.delete(f"run:{run_id}")

    except Exception as e:
        logging.error(f"Erro ao verificar o status da run {run_id} para o agente {agent_id}: {e}")
