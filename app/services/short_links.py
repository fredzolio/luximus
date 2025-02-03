import os
import redis
import string
import secrets
from dotenv import load_dotenv

load_dotenv()

# Configuração da conexão com o Redis
r = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)

def generate_short_code(length: int = 6) -> str:
    """
    Gera um código curto aleatório composto por letras e dígitos.
    """
    caracteres = string.ascii_letters + string.digits
    return ''.join(secrets.choice(caracteres) for _ in range(length))

def create_short_url(long_url: str) -> str:
    """
    Cria um link encurtado para a URL fornecida.

    Parâmetros:
    - long_url: URL original a ser encurtada.
    - base_url: Base da URL do serviço (ex.: "http://localhost:8000").

    Retorna:
    - A URL encurtada completa.
    """
    base_url = os.getenv("SHORT_LINKS_BASE_URL")
    
    short_code = generate_short_code()
    key = f"short:{short_code}"
    
    # Armazena a URL no Redis com expiração de 600 segundos (10 minutos)
    r.setex(key, 600, long_url)
    
    # Monta a URL encurtada garantindo que haja apenas uma barra entre base_url e short_code
    if base_url.endswith('/'):
        return f"{base_url}{short_code}"
    else:
        return f"{base_url}/{short_code}"
