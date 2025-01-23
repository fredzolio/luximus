from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserBase
from app.models.user import User
from app.db.session import SessionLocal


class UserRepository:
    def __init__(self):
        # Gerencia a sessão internamente
        self.db = SessionLocal()

    def create_user(self, user: UserCreate):
        """
        Cria um novo usuário no banco de dados.
        """
        db_user = User(
            name=user.name,
            phone=user.phone,
            cpf=user.cpf
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def get_user_by_id(self, user_id: str):
        """
        Busca um usuário pelo ID.
        """
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_cpf(self, cpf: str):
        """
        Busca um usuário pelo CPF.
        """
        return self.db.query(User).filter(User.cpf == cpf).first()

    def get_user_by_phone(self, phone: str):
        """
        Busca um usuário pelo número de telefone.
        """
        return self.db.query(User).filter(User.phone == phone).first()

    def update_user_by_id(self, user_id: str, user_update: UserBase):
        """
        Atualiza os dados de um usuário com base no ID.
        """
        db_user = self.get_user_by_id(user_id)
        if not db_user:
            return None

        for field, value in user_update.dict(exclude_unset=True).items():
            setattr(db_user, field, value)

        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def update_user_by_cpf(self, cpf: str, user_update: UserBase):
        """
        Atualiza os dados de um usuário com base no CPF.
        """
        db_user = self.get_user_by_cpf(cpf)
        if not db_user:
            return None

        for field, value in user_update.dict(exclude_unset=True).items():
            setattr(db_user, field, value)

        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def delete_user_by_id(self, user_id: str):
        """
        Deleta um usuário com base no ID.
        """
        db_user = self.get_user_by_id(user_id)
        if not db_user:
            return None

        self.db.delete(db_user)
        self.db.commit()
        return db_user

    def delete_user_by_cpf(self, cpf: str):
        """
        Deleta um usuário com base no CPF.
        """
        db_user = self.get_user_by_cpf(cpf)
        if not db_user:
            return None

        self.db.delete(db_user)
        self.db.commit()
        return db_user

    def __exit__(self, exc_type, exc_value, traceback):
        self.db.close()
