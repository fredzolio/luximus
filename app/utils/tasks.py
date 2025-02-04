import time
import logging
from celery import shared_task
import os
from letta_client import MessageCreate, AssistantMessage, ToolCallMessage
from app.utils.celery_imports import lc, get_phone_tag, get_agent_tags
from app.services.whatsapp_service import WhatsAppService
import redis

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
    Tarefa Celery para enviar mensagem ao agente e iniciar o monitoramento da execução.
    """
    try:
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

        # Inicia a verificação do status da execução, com tentativa inicial 1.
        check_run_status_task.delay(run_id, agent_id, timeout=30, poll_interval=1, attempt=1)

    except Exception as e:
        logging.error(f"Erro ao enviar mensagem ao agente {agent_id}: {e}")

@shared_task
def check_run_status_task(run_id: str, agent_id: str, timeout: int = 30, poll_interval: int = 1, attempt: int = 1):
    """
    Tarefa Celery para verificar o status da execução e enviar a resposta ao usuário.
    Em caso de timeout, envia uma mensagem informando que a solicitação está demorando,
    mas continua aguardando a finalização da execução original.
    Para status 'failed', tenta novamente até 4 vezes.
    """
    max_attempts = 4
    timeout_notified = False

    try:
        start_time = time.time()
        phone = redis_client.get(f"run:{run_id}")  # Recupera o telefone do usuário

        if not phone:
            logging.error(f"Telefone do usuário não encontrado para run_id {run_id}.")
            return

        while True:
            run = lc.runs.retrieve_run(run_id)
            if run.status in ["completed", "failed"]:
                break

            # Se o tempo exceder o timeout e o usuário ainda não foi notificado, envia mensagem informativa
            if time.time() - start_time > timeout and not timeout_notified:
                wpp.send_message(
                    phone,
                    "Sua solicitação está demorando mais que o normal, estamos aguardando a finalização."
                )
                timeout_notified = True

            time.sleep(poll_interval)

        # Se a run falhou, tenta novamente (até o máximo de tentativas)
        if run.status == "failed":
            if attempt < max_attempts:
                wpp.send_message(
                    phone,
                    f"A execução falhou. Tentando novamente (tentativa {attempt + 1}/{max_attempts})."
                )
                check_run_status_task.delay(run_id, agent_id, timeout, poll_interval, attempt + 1)
            else:
                logging.error(f"Execução final falhou para o agente {agent_id} após {attempt} tentativas.")
                wpp.send_message(phone, "Erro ao processar a solicitação. Por favor, tente novamente mais tarde.")
            return

        # Se a run foi completada, obtém as mensagens da execução
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
                "start_whatsapp_integration" in tool_called,
                "start_google_integration" in tool_called,
                "verify_integrations_status" in tool_called,
            ])
            if flagged_tools:
                send_message = False

        agent_tags = get_agent_tags(agent_id)
        if "background" in agent_tags:
            send_message = False

        if assistant_message:
            if send_message:
                wpp.send_message(phone, assistant_message)
        else:
            logging.error(f"A resposta do agente {agent_id} não contém 'assistant_message'. Estrutura: {messages}")

        redis_client.delete(f"run:{run_id}")

    except Exception as e:
        logging.error(f"Erro ao verificar o status da run {run_id} para o agente {agent_id}: {e}")
