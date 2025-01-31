from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from starlette.requests import Request
from starlette.responses import RedirectResponse
import os

from app.flows.google_integration_flow import GoogleIntegrationFlow
from app.schemas.user import UserBase
from app.services.user_service import UserRepository
from app.utils.state_utils_jwt import get_user_id_from_state

router = APIRouter(prefix="/google-integration", tags=["GoogleIntegration"])


@router.get("/oauth2callback")
async def oauth2callback(request: Request):
    user_repo = UserRepository()
    
    state = request.query_params.get('state')
    code = request.query_params.get('code')

    if not state or not code:
        return "State or code missing in the callback.", 400

    # Recuperar o user_id a partir do state
    user_id = get_user_id_from_state(state)
    if not user_id:
        return "Invalid state parameter.", 400

    # Carregar o fluxo de integração do usuário
    calendar_flow = GoogleIntegrationFlow(user_id)
    await calendar_flow.load_state()

    scopes = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.compose',
        'https://www.googleapis.com/auth/gmail.readonly'
    ]
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=scopes,
        redirect_uri=os.getenv("OAUTH_REDIRECT_URI")
    )
    flow.fetch_token(code=code)

    credentials = flow.credentials
    
    user_update = UserBase(google_token=credentials.token, google_refresh_token=credentials.refresh_token)
    await user_repo.update_user_by_id(user_id, user_update)

    # Atualizar o estado com os tokens
    calendar_flow.data["tokens"] = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token
    }
    await calendar_flow.save_state()

    # Avançar o fluxo
    await calendar_flow.continue_flow()

    return RedirectResponse('/integration-success')

# async def oauth2callback():
#     state = request.args.get('state')
#     code = request.args.get('code')

#     if not state or not code:
#         return "State or code missing in the callback.", 400

#     # Recuperar o user_id a partir do state
#     user_id = get_user_id_from_state(state)
#     if not user_id:
#         return "Invalid state parameter.", 400

#     # Remover o mapeamento para evitar reutilização
#     del state_user_mapping[state]

#     # Carregar o fluxo de integração do usuário
#     calendar_flow = CalendarIntegrationFlow(user_id)
#     await calendar_flow.load_state()

#     flow = Flow.from_client_secrets_file(
#         'path/to/credentials.json',
#         scopes=['https://www.googleapis.com/auth/calendar'],
#         state=state,
#         redirect_uri=os.getenv("OAUTH_REDIRECT_URI")
#     )
#     flow.fetch_token(code=code)

#     credentials = flow.credentials
#     credentials_json = credentials.to_json()

#     # Atualizar o estado com os tokens
#     calendar_flow.data["tokens"] = {
#         "token": credentials.token,
#         "refresh_token": credentials.refresh_token
#     }
#     await calendar_flow.save_state()

#     # Avançar o fluxo
#     response = await calendar_flow.advance_flow()

#     return redirect('/integration-success')  # Redirecionar para uma página de sucesso