import os
import asyncio
import redis.asyncio as redis

async def reset_redis_db():
    # Constrói a URL de conexão com o Redis
    host = os.getenv("REDIS_HOST", "localhost")
    port = os.getenv("REDIS_PORT", "6379")
    db = os.getenv("REDIS_DB", "0")
    password = os.getenv("REDIS_PASSWORD", "")
    
    if password:
        redis_url = f"redis://:{password}@{host}:{port}/{db}"
    else:
        redis_url = f"redis://{host}:{port}/{db}"
    
    try:
        # Cria a conexão com o Redis
        client = redis.from_url(
            url=redis_url,
            encoding='utf-8',
            decode_responses=True
        )
        print("Conectando ao Redis...")
        await client.ping()
        print("Conectado. Resetando o banco de dados...")
        
        # Reseta (limpa) todos os bancos de dados
        await client.flushall()
        print("Banco de dados resetado com sucesso!")
        
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
    finally:
        if client:
            await client.aclose()

if __name__ == '__main__':
    asyncio.run(reset_redis_db())