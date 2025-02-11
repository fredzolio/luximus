import logging

from letta_client import LlmConfig, ChildToolRule
from app.services.letta_service import lc
from app.utils.system_prompt_text import system_prompt_text

def create_main_agent(user_name: str, user_number: str, human_block_id: str):
    """
    Cria um agente principal e retorna o agente.
    """
    try:
        agent = lc.agents.create(
          agent_type="memgpt_agent",
          name=f"{user_number}_main",
          description=f"Agente principal do usuário, responsável por ser o assistente pessoal do usuário chamado {user_name}",
          context_window_limit=2000000,
          include_base_tools=True,
          tools=[
            "send_message_to_agent_and_wait_for_reply",
            "send_email",
            "list_emails",
            "list_unread_emails",
            "create_event",
            "list_events",
            "update_event",
            "delete_event",
            "list_events_for_week",
            ],
          memory_variables={"user_name": user_name},
          tool_rules=[
            ChildToolRule(tool_name="core_memory_append", children=["send_message"]),
            ChildToolRule(tool_name="archival_memory_insert", children=["send_message"]),
            ChildToolRule(tool_name="core_memory_replace", children=["send_message"]),
            ChildToolRule(tool_name="conversation_search", children=["send_message"]),
            ChildToolRule(tool_name="archival_memory_search", children=["send_message"]),
            ChildToolRule(tool_name="send_email", children=["send_message"]),
            ChildToolRule(tool_name="list_emails", children=["send_message"]),
            ChildToolRule(tool_name="list_unread_emails", children=["send_message"]),
            ChildToolRule(tool_name="create_event", children=["send_message"]),
            ChildToolRule(tool_name="list_events", children=["send_message"]),
            ChildToolRule(tool_name="update_event", children=["send_message"]),
            ChildToolRule(tool_name="delete_event", children=["send_message"]),
            ChildToolRule(tool_name="list_events_for_week", children=["send_message"]),            
            ],
          tags=[
            user_number, 
            "main"
          ],
          llm_config=LlmConfig(
            model= "gemini-1.5-flash",
            model_endpoint_type= "google_ai",
            model_endpoint= "https://generativelanguage.googleapis.com",
            model_wrapper= None,
            context_window= 1000000,
            put_inner_thoughts_in_kwargs= True,
            handle= "google_ai/gemini-1.5-flash"
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
- Quando você não souber uma informação, procure na memória de longo prazo antes de falar ao usuário que não sabe a informação.
- Você sempre deve chamar o usuário pelo primeiro nome.
- Você deve sempre ser educado e gentil.
- Você deve se apresentar como Luximus e dizer que agora, você, o agente principal, será responsável por gerir todas as necessidades do usuário.
- Você é o assistente pessoal do usuário, tem acesso a ferramentas e pode pedir informações a outros agentes para complementar suas informações e contextos para gerenciar a vida do usuário.
- Salve na core memory informações que você julgar extremamente importantes para o usuário.
- Salve na archival memory informações que você julgar importantes para o usuário, mas que não são extremamente importantes.
- Para as funções abaixo peça as informações necessárias (se necessário) ao usuário e chame as funções e aguarde a resposta, organize as informações (se necessário) e retorne ao usuário:            
  - "send_email"
  - "list_emails"
  - "list_unread_emails"
  - "create_event"
  - "list_events"
  - "update_event"
  - "delete_event"
  - "list_events_for_week"
- A não ser que o usuário peça ao contrário, você deve resumir e organizar bem as informações antes de passar ao usuário, use bullet points e listas para organizar as informações mais relevantes e necessárias, se necessário.
- Além disso, você pode pedir informações sobre WhatsApp para o agente background, e somente para essas solicitações (de whatsapp e mensagens) peça sempre salientando a ele para buscar essas informações na memória de longo prazo dele. Pedidos relacionados a e-mail, eventos e outros, peça para o agente background executar a função.
- Você pode pedir informações e conversar com o agente background para entender melhor o contexto do usuário e suas tarefas, necessidades e preferências. O agente background é responsável por ajudar você a entender o contexto do usuário. O agente background é um agente secundário. O agente background tem acesso a informações do usuário que podem ser úteis para você.
\
"""
                },
          ],
        )
        return agent
    except Exception as e:
        logging.error(f"Erro ao criar agente principal: {e}")
        return None