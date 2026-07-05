from fastapi import HTTPException, status

from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def create_user(self, user: UserCreate):
        return self.user_repository.create(user)

    def get_users(self):
        return self.user_repository.get_all()

    def get_user_by_id(self, user_id: int):
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    def update_user(self, user_id: int, user_update: UserUpdate):
         user = self.user_repository.update(user_id, user_update)

         if not user:
          raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

         return user

    def delete_user(self, user_id: int):
         user = self.user_repository.delete(user_id)

         if not user:
          raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

         return user