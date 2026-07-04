from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user: UserCreate) -> User:
        db_user = User(
            name=user.name,
            email=user.email,
        )

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        return db_user
    
    def get_all(self):
        return self.db.query(User).all()
    
    def get_by_id(self, user_id:int):
         return self.db.get(User, user_id)
    
    def update(self, user_id: int, user_update: UserUpdate):
        user = self.get_by_id(user_id)

        if not user:
            return None

        user.name = user_update.name
        user.email = user_update.email

        self.db.commit()
        self.db.refresh(user)

        return user
    
    def delete(self, user_id: int):
        user = self.get_by_id(user_id)

        if not user:
         return None

        self.db.delete(user)
        self.db.commit()

        return user