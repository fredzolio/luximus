from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# URL do banco de dados (assíncrona)
DATABASE_URL = os.getenv("DATABASE_URL")

# Cria o engine assíncrono
engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Configura a sessão assíncrona
SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# Base declarativa para modelos
Base = declarative_base()

# Função para obter uma sessão do banco de dados
async def get_db():
    """
    Gera uma sessão assíncrona para uso no banco de dados.
    Certifique-se de usar `async with` para gerenciar o contexto.
    """
    async with SessionLocal() as session:
        yield session
