from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate


class UserRepository:
    def create(self, db: Session, user: UserCreate) -> User:
        db_user = User(
            name=user.name,
            email=user.email,
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return db_user