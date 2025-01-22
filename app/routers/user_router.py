from fastapi import APIRouter, Depends
from app.schemas.user import UserResponse, UserCreate
from app.services.user_service import create_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserResponse)
def create_new_user(user: UserCreate):
    return create_user(user)
