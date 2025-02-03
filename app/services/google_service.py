import os
import json
import asyncio
import base64
import datetime
from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.services.user_service import UserRepository


def auto_refresh(func):
    """
    Decorator que garante que as credenciais sejam atualizadas
    antes de executar o método.
    """
    def wrapper(self, *args, **kwargs):
        # Se as credenciais estiverem expiradas e houver refresh_token, atualiza-as.
        if self.credentials and self.credentials.expired and self.credentials.refresh_token:
            try:
                # Utilizamos asyncio.run para chamar o método assíncrono.
                asyncio.run(self.refresh_credentials())
            except Exception as e:
                print(f"Erro ao atualizar credenciais: {e}")
        return func(self, *args, **kwargs)
    return wrapper


class GoogleService:
    """
    Serviço para interagir com as APIs do Gmail e Google Calendar.
    """

    def __init__(self, user):
        """
        Inicializa o serviço com os tokens do usuário.

        :param user: Objeto do usuário com os atributos:
                    - id (str): Identificador do usuário.
                    - google_token (str): Token de acesso.
                    - google_refresh_token (str): Token de refresh.
        """
        self.user = user
        credentials_info = {
            "token": user.google_token,
            "refresh_token": user.google_refresh_token,
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "scopes": [
                'https://www.googleapis.com/auth/calendar',
                'https://www.googleapis.com/auth/gmail.modify',
                'https://www.googleapis.com/auth/gmail.compose',
                'https://www.googleapis.com/auth/gmail.readonly'
            ]
        }

        # Cria as credenciais a partir dos dados do usuário.
        self.credentials = Credentials(**credentials_info)

        # Constrói os serviços do Gmail e Calendar.
        self.gmail_service = build('gmail', 'v1', credentials=self.credentials)
        self.calendar_service = build('calendar', 'v3', credentials=self.credentials)

    async def refresh_credentials(self) -> Optional[str]:
        """
        Atualiza as credenciais se estiverem expiradas usando o refresh token
        e atualiza os tokens do usuário no banco de dados via UserRepository.

        :return: JSON com as credenciais atualizadas, se houver atualização, ou None.
        """
        # Cria uma instância do repositório de usuário.
        user_repository = UserRepository()

        if self.credentials and self.credentials.expired and self.credentials.refresh_token:
            self.credentials.refresh(Request())
            updated_credentials_json = self.credentials.to_json()
            tokens = json.loads(updated_credentials_json)
            new_google_token = tokens.get("token")
            # Se o refresh token não for retornado, mantém o atual.
            new_google_refresh_token = tokens.get("refresh_token", self.user.google_refresh_token)

            # Atualiza os tokens do usuário no banco de dados.
            await user_repository.update_google_tokens(
                user_id=self.user.id,
                google_token=new_google_token,
                google_refresh_token=new_google_refresh_token
            )

            # Atualiza os tokens no objeto local também.
            self.user.google_token = new_google_token
            self.user.google_refresh_token = new_google_refresh_token

            return updated_credentials_json
        return None

    # Métodos do Gmail

    @auto_refresh
    def send_email(self, to: str, subject: str, body: str, attachments: Optional[List[str]] = None) -> Optional[str]:
        """
        Envia um email para o destinatário especificado.
        """
        try:
            if attachments:
                message = MIMEMultipart()
                message['to'] = to
                message['subject'] = subject
                message.attach(MIMEText(body, 'plain'))

                for file_path in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    with open(file_path, 'rb') as file:
                        part.set_payload(file.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(file_path)}"')
                    message.attach(part)
            else:
                message = MIMEText(body)
                message['to'] = to
                message['subject'] = subject

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            send_message = {'raw': raw_message}
            sent_message = self.gmail_service.users().messages().send(userId='me', body=send_message).execute()
            print(f"Message Id: {sent_message['id']}")
            return sent_message['id']
        except HttpError as error:
            print(f"An error occurred while sending email: {error}")
            return None

    @auto_refresh
    def list_emails(self, query: Optional[str] = None, max_results: int = 10) -> Optional[List[dict]]:
        """
        Lista os emails do usuário com base em uma query específica.
        """
        try:
            response = self.gmail_service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
            messages = response.get('messages', [])
            email_list = []

            for msg in messages:
                msg_data = self.gmail_service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
                headers = msg_data['payload'].get('headers', [])
                subject = next((header['value'] for header in headers if header['name'] == 'Subject'), 'No Subject')
                sender = next((header['value'] for header in headers if header['name'] == 'From'), 'Unknown Sender')
                snippet = msg_data.get('snippet', '')
                email_list.append({
                    'id': msg['id'],
                    'subject': subject,
                    'from': sender,
                    'snippet': snippet
                })
            return email_list
        except HttpError as error:
            print(f"An error occurred while listing emails: {error}")
            return None

    @auto_refresh
    def list_unread_emails(self, max_results: int = 10) -> Optional[List[dict]]:
        """
        Lista os emails não lidos do usuário.
        """
        query = "is:unread"
        return self.list_emails(query=query, max_results=max_results)

    # Métodos do Google Calendar

    @auto_refresh
    def create_event(self, summary: str, location: str, description: str,
                    start_time: str, end_time: str,
                    attendees: Optional[List[dict]] = None,
                    time_zone: str = 'America/Sao_Paulo') -> Optional[dict]:
        """
        Cria um evento no Google Calendar do usuário.
        """
        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': time_zone,
            },
            'end': {
                'dateTime': end_time,
                'timeZone': time_zone,
            },
            'attendees': attendees if attendees else [],
            'reminders': {
                'useDefault': True,
            },
        }

        try:
            created_event = self.calendar_service.events().insert(calendarId='primary', body=event).execute()
            print(f"Event created: {created_event.get('htmlLink')}")
            return created_event
        except HttpError as error:
            print(f"An error occurred while creating event: {error}")
            return None

    @auto_refresh
    def list_events(self, time_min: Optional[str] = None, time_max: Optional[str] = None,
                    max_results: int = 10) -> Optional[List[dict]]:
        """
        Lista os eventos no Google Calendar do usuário entre time_min e time_max.
        """
        try:
            events_result = self.calendar_service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            event_list = []

            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                event_list.append({
                    'id': event['id'],
                    'summary': event.get('summary', 'No Title'),
                    'location': event.get('location', ''),
                    'description': event.get('description', ''),
                    'start': start,
                    'end': end,
                    'htmlLink': event.get('htmlLink')
                })
            return event_list
        except HttpError as error:
            print(f"An error occurred while listing events: {error}")
            return None

    @auto_refresh
    def update_event(self, event_id: str, updated_fields: dict) -> Optional[dict]:
        """
        Atualiza um evento existente no Google Calendar do usuário.
        """
        try:
            event = self.calendar_service.events().get(calendarId='primary', eventId=event_id).execute()

            for key, value in updated_fields.items():
                if key in event:
                    event[key] = value

            updated_event = self.calendar_service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
            print(f"Event updated: {updated_event.get('htmlLink')}")
            return updated_event
        except HttpError as error:
            print(f"An error occurred while updating event: {error}")
            return None

    @auto_refresh
    def delete_event(self, event_id: str) -> bool:
        """
        Deleta um evento no Google Calendar do usuário.
        """
        try:
            self.calendar_service.events().delete(calendarId='primary', eventId=event_id).execute()
            print(f"Event with ID {event_id} deleted.")
            return True
        except HttpError as error:
            print(f"An error occurred while deleting event: {error}")
            return False

    @auto_refresh
    def list_events_for_week(self, user_timezone: str = 'America/Sao_Paulo') -> Optional[List[dict]]:
        """
        Lista os eventos da próxima semana no Google Calendar do usuário.
        """
        now = datetime.datetime.now()
        start_of_week = now
        end_of_week = now + datetime.timedelta(days=7)

        time_min = start_of_week.isoformat() + 'Z'  # 'Z' indica UTC
        time_max = end_of_week.isoformat() + 'Z'

        return self.list_events(time_min=time_min, time_max=time_max, max_results=50)

    def get_authorization_url(self, client_secrets_file: str, scopes: List[str], redirect_uri: str, state: Optional[str] = None) -> str:
        """
        Gera o URL de autorização para o fluxo OAuth 2.0.
        """
        flow = Flow.from_client_secrets_file(
            client_secrets_file,
            scopes=scopes,
            redirect_uri=redirect_uri
        )

        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=state
        )

        return authorization_url
