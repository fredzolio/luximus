import json
import logging
from httpx import Client
from letta_client import Letta, MessageCreate
import os
from dotenv import load_dotenv

load_dotenv()

custom_httpx_client = Client(headers={"x-bare-password": os.getenv("LETTA_AI_API_PASSWORD")})

lc = Letta(
    base_url=os.getenv("LETTA_AI_API_URL"),
    httpx_client=custom_httpx_client,
)

def extract_message_from_tool_call(tool_call):
    """
    Extrai a mensagem do campo 'arguments' em 'tool_call'.
    """
    arguments = tool_call.arguments
    if not arguments:
        logging.warning("Campo 'arguments' está ausente em 'tool_call'.")
        return None
    try:
        arguments_data = json.loads(arguments)
        return arguments_data.get("message", "Ok, processei essa informação!")
    except json.JSONDecodeError as e:
        logging.error(f"Erro ao decodificar JSON em arguments: {e}")
        return "Erro ao processar a resposta do agente."

def send_user_message_to_agent(agent_id, message):
    """
    Envia uma mensagem para o agente específico via Letta-AI e retorna somente a resposta final.
    """
    try:
        # Envia a mensagem para o agente
        response = lc.agents.messages.create(
            agent_id=agent_id,
            messages=[
                MessageCreate(
                    role="user",
                    text=message,
                )
            ],
        )
        if hasattr(response, 'messages') and response.messages:

            for idx, item in enumerate(response.messages):
                message_type = item.message_type
                if message_type == "assistant_message" and hasattr(item, 'assistant_message'):
                    return item.assistant_message
                if message_type == "tool_call_message" and hasattr(item, 'tool_call'):
                    extracted_message = extract_message_from_tool_call(item.tool_call)
                    if extracted_message:
                        return extracted_message
            logging.warning(f"Nenhuma resposta válida encontrada no retorno do agente {agent_id}.")
            return "Sem resposta final do agente."
        else:
            logging.error(f"A resposta da API para o agente {agent_id} não contém 'messages' ou está vazia.")
            return "Erro ao processar a resposta do agente."

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
