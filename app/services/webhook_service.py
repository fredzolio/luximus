from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user_service import UserRepository

class WebhookService:
    @staticmethod
    async def process_onmessage_event(payload: dict):
        user_name = payload.get('notifyName')
        user_number = payload.get('from').replace("@c.us", "")
        message = payload.get('body')
        session = payload.get('session')

        user = await WebhookService.create_user_if_not_exists(user_number, user_name)

        WebhookService.perform_action_based_on_message(message, user)

        return {
            "user_name": user_name,
            "user_number": user_number,
            "message": message,
            "session": session
        }

    @staticmethod
    async def create_user_if_not_exists(user_number: str, user_name: str):
        user_repo = UserRepository()
        try:
            user = await user_repo.get_user_by_phone(phone=user_number)
            if not user:
                new_user = await user_repo.create_user(user=UserCreate(name=user_name, phone=user_number))
                

                return new_user
            else:
                return user
        except Exception as e:
            print(f"Erro ao criar ou buscar usuário: {e}")

    @staticmethod
    def perform_action_based_on_message(message: str, user: User):
        print(f"{user.name}:\n{message}")
