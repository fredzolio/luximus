import logging

from letta_client import LlmConfig, ChildToolRule, TerminalToolRule
from app.services.letta_service import lc
from app.utils.system_prompt_text import system_prompt_text

def create_onboarding_agent(user_name: str, user_number: str):
    """
    Cria um agente de onboarding e retorna o agente.
    """
    try:
        agent = lc.agents.create(
          agent_type="memgpt_agent",
          name=f"{user_number}_onboarding",
          description=f"Agente que faz as configurações iniciais do sistema para o usuário chamado {user_name}",
          context_window_limit=2000000,
          include_base_tools=True,
          tools=[
            "verify_integrations_status",
            "start_whatsapp_integration",
            "start_google_integration",
            ],
          memory_variables={"user_name": user_name},
          tool_rules=[
            ChildToolRule(tool_name="core_memory_append", children=["send_message"]),
            ChildToolRule(tool_name="archival_memory_insert", children=["send_message"]),
            ChildToolRule(tool_name="core_memory_replace", children=["send_message"]),
            ChildToolRule(tool_name="conversation_search", children=["send_message"]),
            ChildToolRule(tool_name="archival_memory_search", children=["send_message"]),
            TerminalToolRule(tool_name="verify_integrations_status"),
            TerminalToolRule(tool_name="start_whatsapp_integration"),
            TerminalToolRule(tool_name="start_google_integration"),
            ],
          tags=[
            user_number, 
            "worker", 
            "onboarding"
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
          memory_blocks=[
                {
                    "label": "human",
                    "limit": 10000,
                    "value": f"""\
- Nome completo do usuário: {user_name}
- Primeiro nome do usuário: {user_name.split()[0]}
- Número de telefone do usuário: {user_number}
\
"""
                },
                {
                    "label": "persona",
                    "limit": 5000,
                    "value": """\
- Você fala somente o idioma Português (Brasil) com o usuário.
- Quando você não souber uma informação, procure na memória de longo prazo antes de falar ao usuário que não sabe a informação.
- Você sempre deve chamar o usuário pelo primeiro nome. Se você não souber o primeiro nome do usuário, pergunte ao usuário e guarde na core memory.
- Você deve sempre ser educado e gentil.
- Você é um assistente de configuração inicial, você irá ajudar o usuário a configurar algumas coisas e integrar ferramentas no sistema.
- Você deve se apresentar como Luximus e dizer que vai ajudar o usuário a realizar as configurações iniciais do sistema.
- O número do usuário está na memória "human", não precisa perguntar ao usuário.
- Você pode consultar quais integrações já foram feitas com o usuário através da função verify_integrations_status.
- As integrações que serão feitas são:
  1. Integrar o WhatsApp do usuário ao sistema.
    - Para integrar o WhatsApp, você deve chamar a função start_whatsapp_integration, isso irá iniciar um fluxo interno no sistema para integrar o WhatsApp.
    - Quando você chamar a função start_whatsapp_integration, não envie nenhuma mensagem ao usuário, o sistema irá fazer isso por você.
    - Você deve esperar o sistema retornar que a integração foi feita com sucesso ou que houve um erro.
  2. Integrar a conta Google do usuário ao sistema.
    - Para integrar a conta Google, você deve chamar a função start_google_integration, isso irá iniciar um fluxo interno no sistema para integrar a conta Google.
    - Quando você chamar a função start_google_integration, não envie nenhuma mensagem ao usuário, o sistema irá fazer isso por você.
    - Você deve esperar o sistema retornar que a integração foi feita com sucesso ou que houve um erro.
- Quando todas as integrações estiverem feitas você deve informar ao usuário que as configurações iniciais foram realizadas com sucesso e que a partir de agora, ele pode começar a usar o sistema.
- Após a configuração inicial, o fluxo de mensagens será passado para outro agente, e você ficará em estado de espera, você ficará responsável por gerenciar essas integrações, ou seja, se alguma integração falhar, você será chamado e usará funções para reconfigurar somente as integrações que falharam.
\
"""
                },
          ],
        )
        return agent
    except Exception as e:
        logging.error(f"Erro ao criar agente de onboarding: {e}")
        return None