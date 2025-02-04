import asyncio
import json
import re
from typing import Optional
from fastapi import APIRouter, Body, HTTPException, Query, Request

from app.flows.google_integration_flow import GoogleIntegrationFlow
from app.services.google_service import GoogleService
from app.services.letta_service import get_phone_tag
from app.services.user_service import UserRepository
from app.flows.whatsapp_integration_flow import WhatsappIntegrationFlow
import logging

router = APIRouter(prefix="/tools", tags=["Tools"])
logger = logging.getLogger("uvicorn.error")

user_repo = UserRepository()

def validate_phone(phone: str) -> None:
    phone_pattern = re.compile(r'^55\d{10,11}$')
    if not phone:
        logger.error("O número de telefone é obrigatório.")
        raise HTTPException(status_code=400, detail="O número de telefone é obrigatório.")
    if not phone_pattern.match(phone):
        logger.error(f"Formato de telefone inválido: {phone}")
        raise HTTPException(
            status_code=400,
            detail="O número de telefone deve estar no formato DDIDDDNUMERO. Exemplo: 551199999999"
        )
        
async def get_user_by_agent_id(agent_id: str):
    """
    Recupera o usuário associado a um agente com base nas tags.
    """
    try:
        phone = get_phone_tag(agent_id)
        user = await user_repo.get_user_by_phone(phone)
        return user
    except Exception as e:
        logger.error(f"Erro ao recuperar usuário {agent_id}: {e}")

############################################################################################################
# INTEGRATION TOOLS
############################################################################################################

@router.get("/verify-integrations-status")
async def verify_integrations_status(agent_id: str = Query(..., description="ID do agente que chamou a função.")):
        
    user = await get_user_by_agent_id(agent_id)
    
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
async def start_whatsapp_integration(agent_id: str = Query(..., description="ID do agente que chamou a função.")):
        
    user = await get_user_by_agent_id(agent_id)
        
    await user_repo.set_user_integration_running(user.phone, "whatsapp")
    
    flow = WhatsappIntegrationFlow(user_id=user.id)
    
    await flow.load_state()
    
    await flow.restart()
    
    logger.info(f"Fluxo de integração com WhatsApp iniciado para usuário: {user.id}")
    return {"status": "success", "message": "Fluxo de integração com WhatsApp iniciado."}

@router.post("/start-google-integration")
async def start_google_integration(agent_id: str = Query(..., description="ID do agente que chamou a função.")):
        
    user = await get_user_by_agent_id(agent_id)
        
    await user_repo.set_user_integration_running(user.phone, "google_calendar")

    flow = GoogleIntegrationFlow(user.id)
    
    await flow.load_state()
    
    await flow.restart()

    return {"status": "success", "message": "Fluxo de integração com Google iniciado."}

############################################################################################################
# GOOGLE TOOLS
############################################################################################################

@router.post("/send-email")
async def send_email(
    agent_id: str = Query(..., description="ID do agente que chamou a função."),
    to: str = Query(..., description="E-mail de destino"),
    subject: str = Query(..., description="Assunto do e-mail"),
    body: str = Query(..., description="Corpo do e-mail")
):
    """
    Envia um e-mail para o destinatário especificado.
    """
    user = await get_user_by_agent_id(agent_id)

    gs = GoogleService(user)
    try:
        message_id = await asyncio.to_thread(gs.send_email, to=to, subject=subject, body=body)
        return {"status": "success", "message": "E-mail enviado", "id": message_id}
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail: {e}")
        raise HTTPException(status_code=500, detail="Erro ao enviar e-mail.")


@router.get("/list-emails")
async def list_emails(
    agent_id: str = Query(..., description="ID do agente que chamou a função."),
    query: Optional[str] = Query(None, description="Query de busca"),
    max_results: int = Query(10, description="Número máximo de e-mails a retornar")
):
    """
    Lista os e-mails do usuário conforme query.
    """
    user = await get_user_by_agent_id(agent_id)

    gs = GoogleService(user)
    try:
        emails = await asyncio.to_thread(gs.list_emails, query=query, max_results=max_results)
        return {"status": "success", "emails": emails}
    except Exception as e:
        logger.error(f"Erro ao listar e-mails: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar e-mails.")


@router.get("/list-unread-emails")
async def list_unread_emails(
    agent_id: str = Query(..., description="ID do agente que chamou a função."),
    max_results: int = Query(10, description="Número máximo de e-mails não lidos a retornar")
):
    """
    Lista os e-mails não lidos do usuário.
    """
    user = await get_user_by_agent_id(agent_id)

    gs = GoogleService(user)
    try:
        unread_emails = await asyncio.to_thread(gs.list_unread_emails, max_results=max_results)
        return {"status": "success", "emails": unread_emails}
    except Exception as e:
        logger.error(f"Erro ao listar e-mails não lidos: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar e-mails não lidos.")


@router.post("/create-event")
async def create_event(
    agent_id: str = Query(..., description="ID do agente que chamou a função."),
    summary: str = Query(..., description="Título do evento"),
    location: str = Query(..., description="Local do evento"),
    description: str = Query(..., description="Descrição do evento"),
    start_time: str = Query(..., description="Data e hora de início (formato ISO, ex.: 2025-02-10T10:00:00)"),
    end_time: str = Query(..., description="Data e hora de término (formato ISO, ex.: 2025-02-10T12:00:00)"),
    attendees: Optional[str] = Query(None, description="JSON com lista de participantes, ex.: '[{\"email\": \"exemplo@dominio.com\"}]'"),
    time_zone: str = Query("America/Sao_Paulo", description="Fuso horário do evento")
):
    """
    Cria um evento no Google Calendar do usuário.
    """
    user = await get_user_by_agent_id(agent_id)

    gs = GoogleService(user)
    try:
        attendees_list = json.loads(attendees) if attendees else None
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Formato inválido para attendees. Deve ser um JSON válido.")

    try:
        event = await asyncio.to_thread(
            gs.create_event,
            summary=summary,
            location=location,
            description=description,
            start_time=start_time,
            end_time=end_time,
            attendees=attendees_list,
            time_zone=time_zone
        )
        return {"status": "success", "event": event}
    except Exception as e:
        logger.error(f"Erro ao criar evento: {e}")
        raise HTTPException(status_code=500, detail="Erro ao criar evento.")


@router.get("/list-events")
async def list_events(
    agent_id: str = Query(..., description="ID do agente que chamou a função."),
    time_min: Optional[str] = Query(None, description="Data/hora mínima em formato ISO (ex.: 2025-02-01T00:00:00Z)"),
    time_max: Optional[str] = Query(None, description="Data/hora máxima em formato ISO (ex.: 2025-02-07T23:59:59Z)"),
    max_results: int = Query(10, description="Número máximo de eventos a retornar")
):
    """
    Lista os eventos do Google Calendar do usuário dentro do período informado.
    """
    user = await get_user_by_agent_id(agent_id)

    gs = GoogleService(user)
    try:
        events = await asyncio.to_thread(gs.list_events, time_min=time_min, time_max=time_max, max_results=max_results)
        return {"status": "success", "events": events}
    except Exception as e:
        logger.error(f"Erro ao listar eventos: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar eventos.")


@router.put("/update-event")
async def update_event(
    agent_id: str = Query(..., description="ID do agente que chamou a função."),
    event_id: str = Query(..., description="ID do evento a ser atualizado"),
    updated_fields: dict = Body(..., description="Campos a serem atualizados no evento, ex.: {\"summary\": \"Novo título\"}")
):
    """
    Atualiza um evento existente no Google Calendar do usuário.
    """
    user = await get_user_by_agent_id(agent_id)

    gs = GoogleService(user)
    try:
        updated_event = await asyncio.to_thread(gs.update_event, event_id=event_id, updated_fields=updated_fields)
        return {"status": "success", "event": updated_event}
    except Exception as e:
        logger.error(f"Erro ao atualizar evento: {e}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar evento.")


@router.delete("/delete-event")
async def delete_event(
    agent_id: str = Query(..., description="ID do agente que chamou a função."),
    event_id: str = Query(..., description="ID do evento a ser deletado")
):
    """
    Deleta um evento do Google Calendar do usuário.
    """
    user = await get_user_by_agent_id(agent_id)

    gs = GoogleService(user)
    try:
        result = await asyncio.to_thread(gs.delete_event, event_id=event_id)
        if result:
            return {"status": "success", "message": "Evento deletado"}
        else:
            raise HTTPException(status_code=500, detail="Falha ao deletar evento.")
    except Exception as e:
        logger.error(f"Erro ao deletar evento: {e}")
        raise HTTPException(status_code=500, detail="Erro ao deletar evento.")


@router.get("/list-events-for-week")
async def list_events_for_week(
    agent_id: str = Query(..., description="ID do agente que chamou a função."),
    user_timezone: str = Query("America/Sao_Paulo", description="Fuso horário do usuário")
):
    """
    Lista os eventos da próxima semana no Google Calendar do usuário.
    """
    user = await get_user_by_agent_id(agent_id)

    gs = GoogleService(user)
    try:
        events = await asyncio.to_thread(gs.list_events_for_week, user_timezone=user_timezone)
        return {"status": "success", "events": events}
    except Exception as e:
        logger.error(f"Erro ao listar eventos da semana: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar eventos da semana.")


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
        events = gs.send_email(to="fredzolio@live.com", subject="Teste", body="Teste")
        
        return {
            "method": request.method,
            "url": str(request.url),
            "headers": headers,
            "query_params": query_params,
            "body": events
        }

    return await read_request(request)