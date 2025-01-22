from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserBase
from app.models.user import User
from app.db.session import SessionLocal


def create_user(db: Session, user: UserCreate):
    """
    Cria um novo usuário no banco de dados.
    """
    db_user = User(
        id=user.id or None,  # Opcional para o caso de criar o ID manualmente
        name=user.name,
        phone=user.phone,
        cpf=user.cpf,
        is_active=user.is_active if user.is_active is not None else True,
        id_main_agent=user.id_main_agent,
        id_session_wpp=user.id_session_wpp
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_id(db: Session, user_id: str):
    """
    Busca um usuário pelo ID.
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_cpf(db: Session, cpf: str):
    """
    Busca um usuário pelo CPF.
    """
    return db.query(User).filter(User.cpf == cpf).first()


def get_user_by_phone(db: Session, phone: str):
    """
    Busca um usuário pelo número de telefone.
    """
    return db.query(User).filter(User.phone == phone).first()


def update_user_by_id(db: Session, user_id: str, user_update: UserBase):
    """
    Atualiza os dados de um usuário com base no ID.
    """
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None

    # Atualiza os campos fornecidos
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_by_cpf(db: Session, cpf: str, user_update: UserBase):
    """
    Atualiza os dados de um usuário com base no CPF.
    """
    db_user = get_user_by_cpf(db, cpf)
    if not db_user:
        return None

    # Atualiza os campos fornecidos
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user_by_id(db: Session, user_id: str):
    """
    Deleta um usuário com base no ID.
    """
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None

    db.delete(db_user)
    db.commit()
    return db_user


def delete_user_by_cpf(db: Session, cpf: str):
    """
    Deleta um usuário com base no CPF.
    """
    db_user = get_user_by_cpf(db, cpf)
    if not db_user:
        return None

    db.delete(db_user)
    db.commit()
    return db_user
