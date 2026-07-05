from datetime import datetime, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        name: str,
        email: str,
        hashed_password: str,
        role: str,
        status: str,
        department: str | None,
        color: str,
        initials: str,
    ) -> User:
        db_user = User(
            name=name,
            email=email,
            hashed_password=hashed_password,
            role=role,
            status=status,
            department=department,
            color=color,
            initials=initials,
        )

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        return db_user
    
    def get_filtered(
        self,
        search: str | None,
        role: str | None,
        status: str | None,
        page: int,
        per_page: int,
    ) -> tuple[list[User], int]:
        query = self.db.query(User)

        if search:
            like_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    User.name.ilike(like_pattern),
                    User.email.ilike(like_pattern),
                )
            )

        if role:
            query = query.filter(User.role == role)

        if status:
            query = query.filter(User.status == status)

        total = query.count()
        users = (
            query.order_by(User.id)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return users, total
    
    def get_by_id(self, user_id:int):
         return self.db.get(User, user_id)
    
    def update(self, user_id: int, fields: dict) -> User | None:
        user = self.get_by_id(user_id)

        if not user:
            return None

        for key, value in fields.items():
            setattr(user, key, value)

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
    
    def get_by_email(self, email: str):
      return (
        self.db.query(User)
        .filter(User.email == email)
        .first()
    )

    def touch_last_active(self, user: User) -> User:
        user.last_active_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(user)

        return user