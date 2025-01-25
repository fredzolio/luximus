import logging

from letta_client import LlmConfig, ChildToolRule
from app.services.letta_service import lc
from app.utils.system_prompt_text import system_prompt_text

def create_main_agent(user_name: str, user_number: str, human_block_id: str):
    """
    Cria um agente de onboarding e retorna o ID do agente.
    """
    try:
        agent = lc.agents.create(
          agent_type="memgpt_agent",
          name=f"{user_number}_main",
          description=f"Agente principal do usuário, responsável por ser o assistente pessoal do usuário chamado {user_name}",
          context_window_limit=2000000,
          include_base_tools=True,
          # tools=[],
          # tool_ids=[],
          memory_variables={"user_name": user_name},
          tool_rules=[
            ChildToolRule(tool_name="core_memory_append", children=["send_message"]),
            ChildToolRule(tool_name="archival_memory_insert", children=["send_message"]),
            ChildToolRule(tool_name="core_memory_replace", children=["send_message"]),
            ChildToolRule(tool_name="conversation_search", children=["send_message"]),
            ChildToolRule(tool_name="archival_memory_search", children=["send_message"]),           
            ],
          tags=[
            user_number, 
            "main"
          ],
          llm_config=LlmConfig(
            model= "gemini-1.5-pro-latest",
            model_endpoint_type= "google_ai",
            model_endpoint= "https://generativelanguage.googleapis.com",
            model_wrapper= None,
            context_window= 2000000,
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
                    "value": """\
- Você fala somente o idioma Português (Brasil) com o usuário.
- Quando você não souber uma informação, procure na memória de longo prazo antes de falar ao usuário que não sabe a informação.
- Você sempre deve chamar o usuário pelo primeiro nome.
- Você deve sempre ser educado e gentil.
- Você deve se apresentar como Luximus e dizer que agora, você, o agente principal, será responsável por gerir todas as necessidades do usuário.
- Você é o assistente pessoal do usuário, tem acesso a ferramentas e pode pedir informações a outros agentes para complementar suas informações e contextos para gerenciar a vida do usuário.
- Salve na core memory informações que você julgar extremamente importantes para o usuário.
- Salve na archival memory informações que você julgar importantes para o usuário, mas que não são extremamente importantes.
\
"""
                },
          ],
        )
        return agent
    except Exception as e:
        logging.error(f"Erro ao criar agente principal: {e}")
        return None