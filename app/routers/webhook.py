import json
from fastapi import APIRouter, HTTPException, Request

from app.services.webhook_service import WebhookService
from app.utils.integration_manager import whatsapp_session_status_manager

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
            data = await WebhookService.process_onmessage_event(payload)
            return {"status": "success", "event": "onmessage", "data": data}
        
        if payload.get('event') == 'status-find':
            await whatsapp_session_status_manager(payload.get('session'), payload.get('status'))
            return {"status": "success", "event": "status-find"}

        return {"status": "ignored", "message": "Evento não processado."}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Formato de JSON inválido.")
    
# @router.post("/")
# async def webhook_handler(request: Request):
#     try:
#         body = await request.body()
#         print("===== DEBUG WEBHOOK PAYLOAD =====")
#         print(body)
#         return 

#     except json.JSONDecodeError:
#         raise HTTPException(status_code=400, detail="Formato de JSON inválido.")