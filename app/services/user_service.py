from sqlalchemy.orm import Session
from app.schemas.user import UserCreate
from app.models.user import User
from app.db.session import SessionLocal

def create_user(user: UserCreate):
    db = SessionLocal()
    db_user = User(
        name=user.name,
        email=user.email,
        hashed_password=user.password  # Use a função hash aqui
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
