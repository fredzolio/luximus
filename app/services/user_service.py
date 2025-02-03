from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import update, delete
from app.schemas.user import UserCreate, UserBase
from app.models.user import User
from app.db.session import SessionLocal as async_session


class UserRepository:
    async def create_user(self, user: UserCreate):
        """
        Cria um novo usuário no banco de dados.
        """
        async with async_session() as db:
            try:
                db_user = User(
                    name=user.name,
                    phone=user.phone,
                    cpf=user.cpf,
                    is_active=user.is_active,
                    google_calendar_integration=user.google_calendar_integration,
                    apple_calendar_integration=user.apple_calendar_integration,
                    email_integration=user.email_integration,
                    whatsapp_integration=user.whatsapp_integration,
                )
                db.add(db_user)
                await db.commit()
                await db.refresh(db_user)
                return db_user
            except IntegrityError as e:
                await db.rollback()
                raise ValueError(f"Erro ao criar usuário: {e.orig}")

    async def get_user_by_id(self, user_id: str):
        """
        Busca um usuário pelo ID.
        """
        async with async_session() as db:
            query = select(User).where(User.id == user_id)
            result = await db.execute(query)
            return result.scalars().first()

    async def get_user_by_cpf(self, cpf: str):
        """
        Busca um usuário pelo CPF.
        """
        async with async_session() as db:
            query = select(User).where(User.cpf == cpf)
            result = await db.execute(query)
            return result.scalars().first()

    async def get_user_by_phone(self, phone: str):
        """
        Busca um usuário pelo número de telefone.
        """
        async with async_session() as db:
            query = select(User).where(User.phone == phone)
            result = await db.execute(query)
            return result.scalars().first()

    async def update_user_by_id(self, user_id: str, user_update: UserBase):
        """
        Atualiza os dados de um usuário com base no ID.
        """
        async with async_session() as db:
            # Buscar o usuário dentro da mesma sessão
            query = select(User).where(User.id == user_id)
            result = await db.execute(query)
            db_user = result.scalars().first()

            if not db_user:
                raise ValueError(f"Usuário com ID {user_id} não encontrado.")

            # Atualizar os campos definidos em user_update
            update_data = user_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_user, field, value)

            try:
                await db.commit()
                await db.refresh(db_user)
                return db_user
            except IntegrityError as e:
                await db.rollback()
                raise ValueError(f"Erro ao atualizar usuário: {e.orig}")

    async def update_user_by_cpf(self, cpf: str, user_update: UserBase):
        """
        Atualiza os dados de um usuário com base no CPF.
        """
        async with async_session() as db:
            # Buscar o usuário dentro da mesma sessão
            query = select(User).where(User.cpf == cpf)
            result = await db.execute(query)
            db_user = result.scalars().first()

            if not db_user:
                raise ValueError(f"Usuário com CPF {cpf} não encontrado.")

            # Atualizar os campos definidos em user_update
            update_data = user_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_user, field, value)

            try:
                await db.commit()
                await db.refresh(db_user)
                return db_user
            except IntegrityError as e:
                await db.rollback()
                raise ValueError(f"Erro ao atualizar usuário: {e.orig}")

    async def delete_user_by_id(self, user_id: str):
        """
        Deleta um usuário com base no ID.
        """
        async with async_session() as db:
            # Buscar o usuário dentro da mesma sessão
            query = select(User).where(User.id == user_id)
            result = await db.execute(query)
            db_user = result.scalars().first()

            if not db_user:
                raise ValueError(f"Usuário com ID {user_id} não encontrado.")

            try:
                await db.delete(db_user)
                await db.commit()
                return db_user
            except IntegrityError as e:
                await db.rollback()
                raise ValueError(f"Erro ao deletar usuário: {e.orig}")

    async def delete_user_by_cpf(self, cpf: str):
        """
        Deleta um usuário com base no CPF.
        """
        async with async_session() as db:
            # Buscar o usuário dentro da mesma sessão
            query = select(User).where(User.cpf == cpf)
            result = await db.execute(query)
            db_user = result.scalars().first()

            if not db_user:
                raise ValueError(f"Usuário com CPF {cpf} não encontrado.")

            try:
                await db.delete(db_user)
                await db.commit()
                return db_user
            except IntegrityError as e:
                await db.rollback()
                raise ValueError(f"Erro ao deletar usuário: {e.orig}")
    
    async def get_user_integration_is_running(self, phone: str) -> Optional[str]:
        """
        Obtém o status de integração em execução para um usuário baseado no número de telefone.
        """
        async with async_session() as db:
            query = select(User.integration_is_running).where(User.phone == phone)
            result = await db.execute(query)
            return result.scalar_one_or_none()

    async def set_user_integration_running(self, phone: str, msg: Optional[str] = None):
        """
        Define o status de integração em execução para um usuário baseado no número de telefone.
        Se 'msg' não for fornecido, define como None.
        """
        async with async_session() as db:
            # Buscar o usuário dentro da mesma sessão
            query = select(User).where(User.phone == phone)
            result = await db.execute(query)
            db_user = result.scalars().first()

            if not db_user:
                raise ValueError(f"Usuário com número {phone} não encontrado.")

            # Atualizar o campo 'integration_is_running'
            db_user.integration_is_running = msg

            try:
                await db.commit()
                await db.refresh(db_user)
                return db_user
            except IntegrityError as e:
                await db.rollback()
                raise ValueError(f"Erro ao atualizar status de integração: {e.orig}")
            
    async def update_google_tokens(self, user_id: str, google_token: str, google_refresh_token: str):
        """
        Atualiza os tokens do Google de um usuário com base no ID.
        """
        async with async_session() as db:
            query = select(User).where(User.id == user_id)
            result = await db.execute(query)
            db_user = result.scalars().first()

            if not db_user:
                raise ValueError(f"Usuário com ID {user_id} não encontrado.")

            db_user.google_token = google_token
            db_user.google_refresh_token = google_refresh_token

            try:
                await db.commit()
                await db.refresh(db_user)
                return db_user
            except IntegrityError as e:
                await db.rollback()
                raise ValueError(f"Erro ao atualizar tokens: {e.orig}")
