import os
import requests
from dotenv import load_dotenv

class WhatsAppService:
    """
    Serviço para integração com a WPPConnect API.
    Essa classe encapsula chamadas a alguns endpoints básicos
    descritos na OpenAPI, usando requests.
    """
    load_dotenv(dotenv_path=".env", override=True)
    
    def __init__(self, session_name: str, token: str = None):
        """
        :param base_url: URL base do WPPConnect (ex: http://localhost:21465 ou outro endpoint).
        :param session_name: Nome da sessão, ex.: 'NERDWHATS_AMERICA'.
        :param secret_key: Chave secreta usada em alguns endpoints (opcional,
        pois alguns ambientes usam outra forma de autorização).
        """
        self.base_url = os.getenv("WHATSAPP_SERVER_BASE_URL")
        self.session_name = session_name
        self.secret_key = os.getenv("WHATSAPP_SERVER_SECRET_KEY")
        self._token = token

    def generate_token(self):
        """
        Gera o token de acesso (JWT) para uso nos endpoints que requerem bearerAuth.
        Endpoint: POST /api/{session}/{secretkey}/generate-token
        Atualiza self._token internamente.
        """
        if not self.secret_key:
            raise ValueError("secret_key não definido.")

        url = f"{self.base_url}/api/{self.session_name}/{self.secret_key}/generate-token"
        response = requests.post(url)
        response.raise_for_status()
        data = response.json()
        self._token = data.get("token")  
        return self._token

    def _get_headers(self):
        """
        Retorna os cabeçalhos de autorização Bearer, caso haja token.
        """
        if not self._token:
            return {}
        return {"Authorization": f"Bearer {self._token}"}

    def get_qrcode_session(self):
        """
        Obtém o QR Code da sessão. 
        Endpoint: GET /api/{session}/qrcode-session
        """
        url = f"{self.base_url}/api/{self.session_name}/qrcode-session"
        resp = requests.get(url, headers=self._get_headers())
        resp.raise_for_status()
        return resp.json()

    def start_session(self, wait_qr_code: bool = False):
        """
        Inicializa sessão.
        Endpoint: POST /api/{session}/start-session
        """
        url = f"{self.base_url}/api/{self.session_name}/start-session"
        payload = {
            "webhook": os.getenv("WHATSAPP_SERVER_WEBHOOK_URL"),
            "waitQrCode": wait_qr_code
        }
        resp = requests.post(url, json=payload, headers=self._get_headers())
        resp.raise_for_status()
        return resp.json()

    def logout_session(self):
        """
        Faz logout e remove os dados de sessão.
        Endpoint: POST /api/{session}/logout-session
        """
        url = f"{self.base_url}/api/{self.session_name}/logout-session"
        resp = requests.post(url, headers=self._get_headers())
        resp.raise_for_status()
        return resp.json()

    def close_session(self):
        """
        Fecha a sessão sem deletar dados (conforme a doc).
        Endpoint: POST /api/{session}/close-session
        """
        url = f"{self.base_url}/api/{self.session_name}/close-session"
        resp = requests.post(url, headers=self._get_headers())
        resp.raise_for_status()
        return resp.json()

    def status_session(self):
        """
        Verifica status da sessão.
        Endpoint: GET /api/{session}/status-session
        """
        url = f"{self.base_url}/api/{self.session_name}/status-session"
        resp = requests.get(url, headers=self._get_headers())
        resp.raise_for_status()
        return resp.json()

    def download_media(self, message_id: str):
        """
        Faz download de mídia relacionada a uma mensagem específica.
        Endpoint: POST /api/{session}/download-media
        """
        url = f"{self.base_url}/api/{self.session_name}/download-media"
        payload = {"messageId": message_id}
        resp = requests.post(url, json=payload, headers=self._get_headers())
        resp.raise_for_status()
        # Dependendo da implementação, pode vir um base64 ou URL de download
        return resp.json()

    def send_message(self, phone: str, message: str, is_group: bool = False):
        """
        Envia mensagem de texto.
        Endpoint: POST /api/{session}/send-message
        """
        url = f"{self.base_url}/api/{self.session_name}/send-message"
        payload = {
            "phone": phone,
            "isGroup": is_group,
            "message": message
        }
        resp = requests.post(url, json=payload, headers=self._get_headers())
        resp.raise_for_status()
        return resp.json()

    def edit_message(self, message_id: str, new_text: str):
        """
        Edita uma mensagem já enviada (se suportado pelo WA).
        Endpoint: POST /api/{session}/edit-message
        """
        url = f"{self.base_url}/api/{self.session_name}/edit-message"
        payload = {
            "id": message_id,
            "newText": new_text
        }
        resp = requests.post(url, json=payload, headers=self._get_headers())
        resp.raise_for_status()
        return resp.json()

    def send_image(self, phone: str, base64_str: str, filename: str, caption: str, is_group: bool = False):
        """
        Envia imagem em base64.
        Endpoint: POST /api/{session}/send-image
        """
        url = f"{self.base_url}/api/{self.session_name}/send-image"
        payload = {
            "phone": phone,
            "isGroup": is_group,
            "filename": filename,
            "caption": caption,
            "base64": base64_str
        }
        resp = requests.post(url, json=payload, headers=self._get_headers())
        resp.raise_for_status()
        return resp.json()

    def send_reply(self, phone: str, message_id: str, reply_text: str, is_group: bool = False):
        """
        Responde a uma mensagem específica.
        Endpoint: POST /api/{session}/send-reply
        """
        url = f"{self.base_url}/api/{self.session_name}/send-reply"
        payload = {
            "phone": phone,
            "isGroup": is_group,
            "message": reply_text,
            "messageId": message_id
        }
        resp = requests.post(url, json=payload, headers=self._get_headers())
        resp.raise_for_status()
        return resp.json()

    def send_file(self, phone: str, base64_str: str, filename: str, caption: str, is_group: bool = False):
        """
        Envia arquivo em base64.
        Endpoint: POST /api/{session}/send-file
        """
        url = f"{self.base_url}/api/{self.session_name}/send-file"
        payload = {
            "phone": phone,
            "isGroup": is_group,
            "filename": filename,
            "caption": caption,
            "base64": base64_str
        }
        resp = requests.post(url, json=payload, headers=self._get_headers())
        resp.raise_for_status()
        return resp.json()

    def send_file_base64(self, phone: str, base64_str: str, filename: str, caption: str,
                         is_group: bool = False):
        """
        Envia arquivo em base64 (endpoint similar ao send-file; 
        alguns ambientes usam esse separadamente).
        Endpoint: POST /api/{session}/send-file-base64
        """
        url = f"{self.base_url}/api/{self.session_name}/send-file-base64"
        payload = {
            "phone": phone,
            "isGroup": is_group,
            "filename": filename,
            "caption": caption,
            "base64": base64_str
        }
        resp = requests.post(url, json=payload, headers=self._get_headers())
        resp.raise_for_status()
        return resp.json()

    def send_voice(self, phone: str, path_file: str, is_group: bool = False, quoted_message_id: str = None):
        """
        Envia mensagem de voz a partir de um caminho de arquivo local.
        Endpoint: POST /api/{session}/send-voice
        """
        url = f"{self.base_url}/api/{self.session_name}/send-voice"
        payload = {
            "phone": phone,
            "isGroup": is_group,
            "path": path_file
        }
        if quoted_message_id:
            payload["quotedMessageId"] = quoted_message_id

        resp = requests.post(url, json=payload, headers=self._get_headers())
        resp.raise_for_status()
        return resp.json()

    def send_voice_base64(self, phone: str, base64_ptt: str, is_group: bool = False):
        """
        Envia mensagem de voz em base64.
        Endpoint: POST /api/{session}/send-voice-base64
        """
        url = f"{self.base_url}/api/{self.session_name}/send-voice-base64"
        payload = {
            "phone": phone,
            "isGroup": is_group,
            "base64Ptt": base64_ptt
        }
        resp = requests.post(url, json=payload, headers=self._get_headers())
        resp.raise_for_status()
        return resp.json()

    def delete_message(self, phone: str, message_id: str, is_group: bool = False,
                       only_local: bool = False, delete_media_in_device: bool = False):
        """
        Deleta mensagem no WhatsApp. 
        Pode deletar para todos ou apenas para quem deleta, dependendo dos parâmetros.
        Endpoint: POST /api/{session}/delete-message
        """
        url = f"{self.base_url}/api/{self.session_name}/delete-message"
        payload = {
            "phone": phone,
            "isGroup": is_group,
            "messageId": message_id,
            "onlyLocal": only_local,
            "deleteMediaInDevice": delete_media_in_device
        }
        resp = requests.post(url, json=payload, headers=self._get_headers())
        resp.raise_for_status()
        return resp.json()
