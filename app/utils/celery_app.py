# app/utils/celery_app.py

from celery import Celery
import os
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

logger.info(f"Configuração do Celery - Broker: {CELERY_BROKER_URL}, Backend: {CELERY_RESULT_BACKEND}")

celery_app = Celery(
    'worker',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    result_expires=3600,
    broker_connection_retry_on_startup=True,
)

# Autodiscover tasks em app/utils
celery_app.autodiscover_tasks(['app.utils'])
