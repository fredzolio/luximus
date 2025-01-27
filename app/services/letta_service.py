import json
import logging
import re
import time
from httpx import Client
from letta_client import Letta, AsyncLetta, MessageCreate, AssistantMessage
import os
from dotenv import load_dotenv

from app.services.whatsapp_service import WhatsAppService

load_dotenv()

custom_httpx_client = Client(headers={"x-bare-password": os.getenv("LETTA_AI_API_PASSWORD")})

lc = Letta(
    base_url=os.getenv("LETTA_AI_API_URL"),
    httpx_client=custom_httpx_client,
)

wpp = WhatsAppService(session_name="principal", token=os.getenv("PRINCIPAL_WPP_SESSION_TOKEN"))

def send_user_message_to_agent(agent_id, message, timeout=15):
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
            return "Erro ao processar a mensagem: ID da resposta não encontrado."

        start_time = time.time()
        run_done = False

        while not run_done:
            run = lc.runs.retrieve_run(response.id)
            if run.status in ["completed", "failed"]:
                run_done = True
            if time.time() - start_time > timeout:
                logging.error(f"Timeout ao aguardar a execução do agente {agent_id}.")
                return "Processando a sua solicitação. 😊"
    
        messages = lc.runs.list_run_messages(response.id)
        assistant_message = next(
            (msg.content for msg in messages if isinstance(msg, AssistantMessage)),
            None
        )
        if assistant_message:
            return assistant_message
        else:
            logging.error(f"A resposta do agente {agent_id} não contém 'assistant_message'. Estrutura: {messages}")
            return "Erro: Não foi possível encontrar a mensagem do agente."

    except Exception as e:
        logging.error(f"Erro ao enviar mensagem ao agente {agent_id}: {e}")
        return "Desculpe, ocorreu um erro ao processar sua mensagem."
    
def send_system_message_to_agent(agent_id, message, timeout=30):
    try:
        # Enviar mensagem ao agente
        lc.agents.messages.create_async(
            agent_id=agent_id,
            messages=[
                MessageCreate(
                    role="system",
                    content=message,
                )
            ],
        )
    except Exception as e:
        logging.error(f"Erro ao enviar mensagem ao agente {agent_id}: {e}")
        return "Desculpe, ocorreu um erro ao processar sua mensagem."

def get_onboarding_agent_id(user_number: str):
    """
    Retorna o ID do agente de onboarding do usuário.
    """
    try:
        agents = lc.agents.list(tags=[user_number, "worker", "onboarding"])
        agent_id = [agent.id for agent in agents]
        if agent_id:
            return agent_id[0]
        logging.warning(f"Nenhum agente de onboarding encontrado para o usuário {user_number}.")
        return None
    except Exception as e:
        logging.error(f"Erro ao buscar agente de onboarding para o usuário {user_number}: {e}")
        return None

def get_human_block_id(agent_id: str):
    """
    Retorna o ID do bloco humano associado ao agente.
    """
    try:
        block = lc.agents.core_memory.retrieve_block(agent_id, "human")
        if block.id:
            return block.id
        logging.warning(f"Nenhum bloco humano encontrado para o agente {agent_id}.")
        return None
    except Exception as e:
        logging.error(f"Erro ao buscar bloco humano para o agente {agent_id}: {e}")
        return None
    
def get_phone_tag(tags):
    for tag in tags:
        if re.search(r'\d+', tag):
            return tag
    return None