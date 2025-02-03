import re
from fastapi import APIRouter, HTTPException, Query, Request

from app.flows.google_integration_flow import GoogleIntegrationFlow
from app.services.google_service import GoogleService
from app.services.user_service import UserRepository
from app.flows.whatsapp_integration_flow import WhatsappIntegrationFlow
import logging

router = APIRouter(prefix="/tools", tags=["Tools"])
logger = logging.getLogger("uvicorn.error")


############################################################################################################
# INTEGRATION TOOLS
############################################################################################################

@router.get("/verify-integrations-status")
async def verify_integrations_status(phone: str = Query(..., description="Número de telefone no formato '551199999999'")):
    """
    Verifica o status das integrações.
    """
    phone_pattern = re.compile(r'^55\d{10,11}$')
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
    
    status = "pending"
    
    is_user_fully_integrated = all([
        user.whatsapp_integration,
        user.apple_calendar_integration,
        user.google_calendar_integration,
        user.email_integration
    ])
    
    if is_user_fully_integrated:
        status = "completed"
    
    return {
        "status": f"{status}",
        "integrations": integrations
    }

@router.post("/start-whatsapp-integration")
async def start_whatsapp_integration(phone: str = Query(..., description="Número de telefone no formato '551199999999'")):
    """
    Inicia a integração com o WhatsApp recebendo o número de telefone via query parameters.
    """

    # Validação do número de telefone
    phone_pattern = re.compile(r'^55\d{10,11}$')
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

@router.post("/start-google-integration")
async def start_google_integration(phone: str = Query(..., description="Número de telefone no formato '551199999999'")):

    phone_pattern = re.compile(r'^55\d{10,11}$')
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
        
    await user_repo.set_user_integration_running(user.phone, "google_calendar")

    flow = GoogleIntegrationFlow(user.id)
    
    await flow.load_state()
    
    await flow.restart()

    return {"status": "success", "message": "Fluxo de integração com Google iniciado."}

############################################################################################################
# GOOGLE TOOLS
############################################################################################################







############################################################################################################
# TEST TOOLS
############################################################################################################

@router.post("/teste")
async def teste(request: Request):
    async def read_request(request: Request):
        body = await request.body()
        headers = dict(request.headers)
        query_params = dict(request.query_params)
        user_repo = UserRepository()
        user = await user_repo.get_user_by_phone('553185482592')
        gs = GoogleService(user)
        events = gs.list_events()
        
        return {
            "method": request.method,
            "url": str(request.url),
            "headers": headers,
            "query_params": query_params,
            "body": events
        }

    return await read_request(request)