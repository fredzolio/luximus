import json
from fastapi import APIRouter, HTTPException, Request

from app.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhook", tags=["Webhook"])

@router.post("/")
async def webhook_handler(request: Request):
    """
    Rota para receber eventos e processar apenas mensagens (onmessage).
    """
    try:
        body = await request.body()
        if not body:
            raise HTTPException(status_code=400, detail="O corpo da requisição está vazio.")

        payload = json.loads(body.decode("utf-8"))

        if payload.get('event') == 'onmessage':
            data = WebhookService.process_onmessage_event(payload)
            return {"status": "success", "event": "onmessage", "data": data}

        return {"status": "ignored", "message": "Evento não processado."}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Formato de JSON inválido.")