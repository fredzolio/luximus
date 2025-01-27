import logging
import re
from letta_client import  MessageCreate
from app.utils.tasks import send_message_task

from app.utils.celery_imports import lc

def send_user_message_to_agent(agent_id: str, message: str):
    """
    Envia uma mensagem ao agente e processa a resposta de forma assíncrona.
    """
    try:
        # Enfileirar a tarefa Celery
        send_message_task.delay(agent_id, message)
        return "Sua mensagem está sendo processada. Você será notificado assim que receber uma resposta."
    except Exception as e:
        logging.error(f"Erro ao enfileirar a tarefa: {e}")
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
    
def get_phone_tag(agent_id: str):
    agent = lc.agents.retrieve(agent_id)
    tags = agent.tags
    for tag in tags:
        if re.search(r'\d+', tag):
            return tag
    return None