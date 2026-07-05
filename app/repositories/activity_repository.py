from sqlalchemy.orm import Session

from app.models.activity import Activity


class ActivityRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        type: str,
        user_id: int,
        message: str,
        project_id: int | None = None,
        task_id: int | None = None,
    ) -> Activity:
        activity = Activity(
            type=type,
            user_id=user_id,
            project_id=project_id,
            task_id=task_id,
            message=message,
        )

        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)

        return activity

    def get_filtered(
        self,
        *,
        project_id: int | None = None,
        task_id: int | None = None,
        type: str | None = None,
        user_id: int | None = None,
        visible_project_ids: list[int] | None = None,
        page: int,
        per_page: int,
    ) -> tuple[list[Activity], int]:
        query = self.db.query(Activity)

        if project_id is not None:
            query = query.filter(Activity.project_id == project_id)

        if task_id is not None:
            query = query.filter(Activity.task_id == task_id)

        if type:
            query = query.filter(Activity.type == type)

        if user_id is not None:
            query = query.filter(Activity.user_id == user_id)

        # Restricts a non-privileged caller's view (e.g. dashboard feed) to
        # only activities belonging to projects they can actually see.
        if visible_project_ids is not None:
            query = query.filter(Activity.project_id.in_(visible_project_ids))

        total = query.count()
        activities = (
            query.order_by(Activity.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return activities, total
