import re
from fastapi import APIRouter, HTTPException, Query

from app.services.user_service import UserRepository
from app.flows.whatsapp_integration_flow import WhatsappIntegrationFlow
import logging

router = APIRouter(prefix="/tools", tags=["Tools"])
logger = logging.getLogger("uvicorn.error")

@router.get("/verify-integrations-status")
async def verify_integrations_status(phone: str = Query(..., description="Número de telefone no formato '551199999999'")):
    """
    Verifica o status das integrações.
    """
    phone_pattern = re.compile(r'^55\d{10}$')
    if not phone:
        logger.error("O número de telefone é obrigatório.")
        raise HTTPException(status_code=400, detail="O número de telefone é obrigatório.")
    if not phone_pattern.match(phone):
        logger.error(f"Formato de telefone inválido: {phone}")
        raise HTTPException(
            status_code=400,
            detail="O número de telefone deve estar no formato DDIDDDNUMERO.\nExemplo: 5511999999999"
        )
    user_repo = UserRepository()
    user = await user_repo.get_user_by_phone(phone)
    
    integrations = {
        "whatsapp": user.whatsapp_integration,
        "google_calendar": user.google_calendar_integration,
        "apple_calendar": user.apple_calendar_integration,
        "email": user.email_integration
    }
    
    return {
        "status": "success",
        "integrations": integrations
    }

@router.post("/start-whatsapp-integration")
async def start_whatsapp_integration(phone: str = Query(..., description="Número de telefone no formato '551199999999'")):
    """
    Inicia a integração com o WhatsApp recebendo o número de telefone via query parameters.
    """

    # Validação do número de telefone
    phone_pattern = re.compile(r'^55\d{10}$')
    if not phone:
        logger.error("O número de telefone é obrigatório.")
        raise HTTPException(status_code=400, detail="O número de telefone é obrigatório.")
    if not phone_pattern.match(phone):
        logger.error(f"Formato de telefone inválido: {phone}")
        raise HTTPException(
            status_code=400,
            detail="O número de telefone deve estar no formato DDIDDDNUMERO.\nExemplo: 551199999999"
        )
    
    user_repo = UserRepository()

    user = await user_repo.get_user_by_phone(phone)
    if not user:
        logger.error(f"Usuário não encontrado para o telefone: {phone}")
        raise HTTPException(
            status_code=200,
            detail="Usuário não encontrado para o número de telefone fornecido."
        )
        
    await user_repo.set_user_integration_running(user.phone, "whatsapp")
    
    flow = WhatsappIntegrationFlow(user_id=user.id)
    
    await flow.load_state()
    
    await flow.restart()
    
    logger.info(f"Fluxo de integração com WhatsApp iniciado para usuário: {user.id}")
    return {"status": "success", "message": "Fluxo de integração com WhatsApp iniciado."}
