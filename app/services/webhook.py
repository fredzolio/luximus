import json
from fastapi import APIRouter, HTTPException, Request

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
            user_name = payload.get('notifyName')
            user_number = payload.get('from')
            message = payload.get('body') 
            
            clean_number = user_number.replace("@c.us", "")
            
            print(f"Evento: onmessage")
            print(f"Nome do usuário: {user_name}")
            print(f"Número do usuário: {clean_number}")
            print(f"Mensagem: {message}")

            # Retorna a resposta com os dados extraídos
            return {
                "status": "success",
                "event": "onmessage",
                "data": {
                    "user_name": user_name,
                    "user_number": clean_number,
                    "message": message,
                },
            }

        return {"status": "ignored", "message": "Evento não processado."}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Formato de JSON inválido.")
