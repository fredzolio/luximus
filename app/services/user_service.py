from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.schemas.user import UserCreate, UserBase
from app.models.user import User
from app.db.session import SessionLocal as async_session


class UserRepository:
    async def create_user(self, user: UserCreate):
        """
        Cria um novo usuário no banco de dados.
        """
        async with async_session() as db:
            db_user = User(
                name=user.name,
                phone=user.phone,
                cpf=user.cpf
            )
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
            return db_user

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
            db_user = await self.get_user_by_id(user_id)
            if not db_user:
                return None

            for field, value in user_update.model_dump(exclude_unset=True).items():
                setattr(db_user, field, value)

            await db.commit()
            await db.refresh(db_user)
            return db_user

    async def update_user_by_cpf(self, cpf: str, user_update: UserBase):
        """
        Atualiza os dados de um usuário com base no CPF.
        """
        async with async_session() as db:
            db_user = await self.get_user_by_cpf(cpf)
            if not db_user:
                return None

            for field, value in user_update.model_dump(exclude_unset=True).items():
                setattr(db_user, field, value)

            await db.commit()
            await db.refresh(db_user)
            return db_user

    async def delete_user_by_id(self, user_id: str):
        """
        Deleta um usuário com base no ID.
        """
        async with async_session() as db:
            db_user = await self.get_user_by_id(user_id)
            if not db_user:
                return None

            await db.delete(db_user)
            await db.commit()
            return db_user

    async def delete_user_by_cpf(self, cpf: str):
        """
        Deleta um usuário com base no CPF.
        """
        async with async_session() as db:
            db_user = await self.get_user_by_cpf(cpf)
            if not db_user:
                return None

            await db.delete(db_user)
            await db.commit()
            return db_user
