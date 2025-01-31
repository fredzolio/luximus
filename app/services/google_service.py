# app/services/google_service.py

import os
import json
from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import datetime

class GoogleService:
    """
    Serviço para interagir com as APIs do Gmail e Google Calendar.
    """

    def __init__(self, credentials_json: str):
        """
        Inicializa o serviço com as credenciais do usuário.
        
        :param credentials_json: JSON string contendo as credenciais OAuth 2.0 do usuário.
        """
        
        # Descriptografar as credenciais
        self.credentials = Credentials.from_authorized_user_info(json.loads(credentials_json))
        
        # Construir os serviços do Gmail e Calendar
        self.gmail_service = build('gmail', 'v1', credentials=self.credentials)
        self.calendar_service = build('calendar', 'v3', credentials=self.credentials)

    def refresh_credentials(self):
        """
        Atualiza as credenciais se estiverem expiradas usando o refresh token.
        """
        if self.credentials and self.credentials.expired and self.credentials.refresh_token:
            self.credentials.refresh(Request())
            # Atualizar as credenciais criptografadas
            updated_credentials_json = self.credentials.to_json()
            return updated_credentials_json
        return None

    # Métodos do Gmail

    def send_email(self, to: str, subject: str, body: str, attachments: Optional[List[str]] = None) -> Optional[str]:
        """
        Envia um email para o destinatário especificado.
        
        :param to: Endereço de email do destinatário.
        :param subject: Assunto do email.
        :param body: Corpo do email em texto simples.
        :param attachments: Lista de caminhos para arquivos a serem anexados (opcional).
        :return: ID da mensagem enviada ou None em caso de erro.
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

    def list_emails(self, query: Optional[str] = None, max_results: int = 10) -> Optional[List[dict]]:
        """
        Lista os emails do usuário com base em uma query específica.
        
        :param query: Query para filtrar emails (opcional).
        :param max_results: Número máximo de emails a serem retornados.
        :return: Lista de dicionários contendo informações dos emails ou None em caso de erro.
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

    def list_unread_emails(self, max_results: int = 10) -> Optional[List[dict]]:
        """
        Lista os emails não lidos do usuário.
        
        :param max_results: Número máximo de emails a serem retornados.
        :return: Lista de dicionários contendo informações dos emails ou None em caso de erro.
        """
        query = "is:unread"
        return self.list_emails(query=query, max_results=max_results)

    # Métodos do Google Calendar

    def create_event(self, summary: str, location: str, description: str,
                    start_time: str, end_time: str,
                    attendees: Optional[List[dict]] = None,
                    time_zone: str = 'America/Sao_Paulo') -> Optional[dict]:
        """
        Cria um evento no Google Calendar do usuário.
        
        :param summary: Título do evento.
        :param location: Local do evento.
        :param description: Descrição do evento.
        :param start_time: Início do evento no formato 'YYYY-MM-DDTHH:MM:SS±HH:MM'.
        :param end_time: Término do evento no formato 'YYYY-MM-DDTHH:MM:SS±HH:MM'.
        :param attendees: Lista de dicionários com os emails dos participantes, por exemplo: [{'email': 'example@example.com'}]
        :param time_zone: Fuso horário do evento.
        :return: Dicionário com detalhes do evento criado ou None em caso de erro.
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

    def list_events(self, time_min: Optional[str] = None, time_max: Optional[str] = None,
                  max_results: int = 10) -> Optional[List[dict]]:
        """
        Lista os eventos no Google Calendar do usuário entre time_min e time_max.
        
        :param time_min: Data e hora mínima no formato 'YYYY-MM-DDTHH:MM:SSZ' (UTC) ou 'YYYY-MM-DDTHH:MM:SS±HH:MM'.
        :param time_max: Data e hora máxima no formato 'YYYY-MM-DDTHH:MM:SSZ' (UTC) ou 'YYYY-MM-DDTHH:MM:SS±HH:MM'.
        :param max_results: Número máximo de eventos a serem retornados.
        :return: Lista de dicionários contendo informações dos eventos ou None em caso de erro.
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

    def update_event(self, event_id: str, updated_fields: dict) -> Optional[dict]:
        """
        Atualiza um evento existente no Google Calendar do usuário.
        
        :param event_id: ID do evento a ser atualizado.
        :param updated_fields: Dicionário com os campos a serem atualizados, por exemplo: {'summary': 'Novo Título'}
        :return: Dicionário com detalhes do evento atualizado ou None em caso de erro.
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

    def delete_event(self, event_id: str) -> bool:
        """
        Deleta um evento no Google Calendar do usuário.
        
        :param event_id: ID do evento a ser deletado.
        :return: True se a deleção for bem-sucedida, False caso contrário.
        """
        try:
            self.calendar_service.events().delete(calendarId='primary', eventId=event_id).execute()
            print(f"Event with ID {event_id} deleted.")
            return True
        except HttpError as error:
            print(f"An error occurred while deleting event: {error}")
            return False

    def list_events_for_week(self, user_timezone: str = 'America/Sao_Paulo') -> Optional[List[dict]]:
        """
        Lista os eventos da próxima semana no Google Calendar do usuário.
        
        :param user_timezone: Fuso horário do usuário.
        :return: Lista de dicionários contendo informações dos eventos ou None em caso de erro.
        """
        now = datetime.datetime.utcnow()
        start_of_week = now
        end_of_week = now + datetime.timedelta(days=7)

        time_min = start_of_week.isoformat() + 'Z'  # 'Z' indica UTC
        time_max = end_of_week.isoformat() + 'Z'

        return self.list_events(time_min=time_min, time_max=time_max, max_results=50)

    # Métodos Adicionais (Receber Emails via Push ou Polling) podem ser implementados conforme a necessidade.

    # Método para Gerar URL de Autorização (Utilizado no fluxo OAuth)
    def get_authorization_url(self, client_secrets_file: str, scopes: List[str], redirect_uri: str, state: Optional[str] = None) -> str:
        """
        Gera o URL de autorização para o fluxo OAuth 2.0.
        
        :param client_secrets_file: Caminho para o arquivo client_secret.json.
        :param scopes: Lista de scopes para solicitar.
        :param redirect_uri: URI de redirecionamento após a autorização.
        :param state: Parâmetro opcional para manter o estado entre a solicitação e a callback.
        :return: URL de autorização.
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
