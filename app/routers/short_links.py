import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
import redis

router = APIRouter(prefix="/temps", tags=["TempShortLinks"])
logger = logging.getLogger("uvicorn.error")

# Configuração da conexão com o Redis
r = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)

@router.get("/{short_code}")
def redirect_short_url(short_code: str):
    key = f"short:{short_code}"
    long_url = r.get(key)
    if long_url:
        return RedirectResponse(url=long_url)
    else:
        raise HTTPException(status_code=404, detail="URL não encontrada ou expirou")
