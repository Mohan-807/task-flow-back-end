from sqlalchemy.orm import Session

from app.models.comment import Comment


class CommentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, task_id: int, user_id: int, content: str) -> Comment:
        comment = Comment(task_id=task_id, user_id=user_id, content=content)

        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)

        return comment

    def get_by_id(self, comment_id: int) -> Comment | None:
        return self.db.get(Comment, comment_id)

    def get_filtered(
        self,
        *,
        task_id: int,
        page: int,
        per_page: int,
    ) -> tuple[list[Comment], int]:
        query = self.db.query(Comment).filter(Comment.task_id == task_id)

        total = query.count()
        comments = (
            query.order_by(Comment.created_at)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return comments, total

    def update(self, comment_id: int, fields: dict) -> Comment | None:
        comment = self.get_by_id(comment_id)
        if not comment:
            return None

        for key, value in fields.items():
            setattr(comment, key, value)

        self.db.commit()
        self.db.refresh(comment)

        return comment

    def delete(self, comment_id: int) -> Comment | None:
        comment = self.get_by_id(comment_id)
        if not comment:
            return None

        self.db.delete(comment)
        self.db.commit()

        return comment
