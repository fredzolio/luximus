from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user_service import UserRepository

class WebhookService:
    @staticmethod
    def process_onmessage_event(payload: dict):
        user_name = payload.get('notifyName')
        user_number = payload.get('from').replace("@c.us", "")
        message = payload.get('body')

        user = WebhookService.create_user_if_not_exists(user_number, user_name)

        WebhookService.perform_action_based_on_message(message, user)

        return {
            "user_name": user_name,
            "user_number": user_number,
            "message": message,
        }

    @staticmethod
    def create_user_if_not_exists(user_number: str, user_name: str):
        user_repo = UserRepository()
        try:
            user = user_repo.get_user_by_phone(phone=user_number)
            if not user:
                new_user = user_repo.create_user(user=UserCreate(name=user_name, phone=user_number))
                print(f"Usuário criado: {new_user}")
                return new_user
            else:
                print(f"Usuário já existe: {user}")
                return user
        except Exception as e:
            print(f"Erro ao criar ou buscar usuário: {e}")

    @staticmethod
    def perform_action_based_on_message(message: str, user: User):
        if message.lower() == "oi":
            print(f"Usuário {user.name} disse 'Oi', envie uma resposta!")
