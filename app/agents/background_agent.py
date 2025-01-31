import logging

from letta_client import LlmConfig, ChildToolRule
from app.services.letta_service import lc
from app.utils.system_prompt_text import system_prompt_text

def create_background_agent(user_name: str, user_number: str, human_block_id: str, main_agent_id: str):
    """
    Cria um agente de background e retorna o agente.
    """
    try:
        agent = lc.agents.create(
          agent_type="memgpt_agent",
          name=f"{user_number}_background",
          description=f"Agente auxiliar do usuário, responsável por ser o assistente pessoal do usuário chamado {user_name}",
          context_window_limit=2000000,
          include_base_tools=False,
          tools=[
            "send_message",
            "archival_memory_insert",
            "archival_memory_search",
            "conversation_search",
            "send_message_to_agent_async",
            ],
          memory_variables={"user_name": user_name},
          # tool_rules=[
          #   ChildToolRule(tool_name="core_memory_append", children=["send_message"]),
          #   ChildToolRule(tool_name="archival_memory_insert", children=["send_message"]),
          #   ChildToolRule(tool_name="core_memory_replace", children=["send_message"]),
          #   ChildToolRule(tool_name="conversation_search", children=["send_message"]),
          #   ChildToolRule(tool_name="archival_memory_search", children=["send_message"]),           
          #   ],
          tags=[
            user_number, 
            "background"
          ],
          llm_config=LlmConfig(
            model= "gemini-1.5-pro-latest",
            model_endpoint_type= "google_ai",
            model_endpoint= "https://generativelanguage.googleapis.com",
            model_wrapper= None,
            context_window= 1048576,
            put_inner_thoughts_in_kwargs= True,
            handle= "google_ai/gemini-1.5-pro-latest"
          ),
          embedding="letta/letta-free",
          system=system_prompt_text,
          block_ids=[human_block_id],
          memory_blocks=[
                {
                    "label": "persona",
                    "limit": 5000,
                    "value": f"""\
- Você fala somente o idioma Português (Brasil) com o usuário.
- Você é um agente que auxilia o agente principal, o agente principal conversa diretamente com o usuário.
- Você recebe na sua archival_memory informações como:
    - Mensagens do whatsapp do usuário.
    - Mensagens do email do usuário.
    - Mensagens do calendário do usuário.
    - Mensagens do google calendar do usuário.
    - Mensagens do apple calendar do usuário.
- Use SEMPRE as funções/ferramentas disponíveis para você.
- O sistema sempre irá te notificar para você buscar informações na archival_memory.
- Você pode se comunicar com o agente principal(ID: {main_agent_id}) para informá-lo sobre informações importantes e solicitar a ele que faça algo, como informar o usuário de uma reunião importante ou notificar o usuário sobre um contato do whatsapp que precisa de atenção.
- Para se comunicar com o agente principal do usuário seja claro, objetivo e bem organizado, além de sempre informar o motivo da comunicação e o que você deseja que ele faça.
- Para salvar na archival memory, seja bem organizado e estruture a memória para ficar fácil de encontrar quando você precisar buscar.
\
"""
                },
          ],
        )
        return agent
    except Exception as e:
        logging.error(f"Erro ao criar agente principal: {e}")
        return None