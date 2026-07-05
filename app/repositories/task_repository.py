from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.task import Task


class TaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_max_column_order(self, project_id: int, status: str) -> int:
        max_order = (
            self.db.query(func.max(Task.column_order))
            .filter(Task.project_id == project_id, Task.status == status)
            .scalar()
        )
        return max_order if max_order is not None else -1

    def create(
        self,
        *,
        project_id: int,
        title: str,
        description: str | None,
        status: str,
        priority: str,
        assignee_id: int | None,
        reporter_id: int,
        due_date: date | None,
        tags: list[str],
    ) -> Task:
        column_order = self.get_max_column_order(project_id, status) + 1

        task = Task(
            project_id=project_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
            reporter_id=reporter_id,
            due_date=due_date,
            tags=tags,
            column_order=column_order,
        )

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        return task

    def get_by_id(self, task_id: int) -> Task | None:
        return self.db.get(Task, task_id)

    def get_filtered(
        self,
        *,
        project_id: int,
        status: str | None,
        priority: str | None,
        assignee_id: int | None,
        search: str | None,
        page: int,
        per_page: int,
    ) -> tuple[list[Task], int]:
        query = self.db.query(Task).filter(Task.project_id == project_id)

        if status:
            query = query.filter(Task.status == status)

        if priority:
            query = query.filter(Task.priority == priority)

        if assignee_id is not None:
            query = query.filter(Task.assignee_id == assignee_id)

        if search:
            query = query.filter(Task.title.ilike(f"%{search}%"))

        total = query.count()
        tasks = (
            query.order_by(Task.status, Task.column_order, Task.created_at)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return tasks, total

    def update(self, task_id: int, fields: dict) -> Task | None:
        task = self.get_by_id(task_id)
        if not task:
            return None

        for key, value in fields.items():
            setattr(task, key, value)

        self.db.commit()
        self.db.refresh(task)

        return task

    def delete(self, task_id: int) -> Task | None:
        task = self.get_by_id(task_id)
        if not task:
            return None

        # Detach (not delete) this task's activity history first: those rows
        # still belong to the project's audit trail (Activity.project_id is
        # untouched), they just can no longer deep-link to a task that's gone.
        self.db.query(Activity).filter(Activity.task_id == task_id).update(
            {Activity.task_id: None}
        )

        self.db.delete(task)
        self.db.commit()

        return task

    def get_by_project_ordered(self, project_id: int) -> list[Task]:
        return (
            self.db.query(Task)
            .filter(Task.project_id == project_id)
            .order_by(Task.status, Task.column_order)
            .all()
        )

    def get_recent(self, project_ids: list[int] | None, limit: int) -> list[Task]:
        query = self.db.query(Task)

        if project_ids is not None:
            query = query.filter(Task.project_id.in_(project_ids))

        return query.order_by(Task.updated_at.desc()).limit(limit).all()

    def move(self, task: Task, new_status: str, new_order: int) -> Task:
        old_status = task.status
        old_order = task.column_order

        if old_status == new_status:
            # Reordering within the same column: only the tasks strictly
            # between the old and new position need to shift, one step, to
            # close the gap the move leaves and open a gap at the target.
            if new_order > old_order:
                self._shift_column(
                    project_id=task.project_id,
                    status=old_status,
                    exclude_task_id=task.id,
                    lower=old_order,
                    upper=new_order,
                    lower_inclusive=False,
                    upper_inclusive=True,
                    delta=-1,
                )
            elif new_order < old_order:
                self._shift_column(
                    project_id=task.project_id,
                    status=old_status,
                    exclude_task_id=task.id,
                    lower=new_order,
                    upper=old_order,
                    lower_inclusive=True,
                    upper_inclusive=False,
                    delta=1,
                )
        else:
            # Moving to a different column: compact the gap left behind in
            # the source column, then open a gap at the target position in
            # the destination column.
            self._shift_column(
                project_id=task.project_id,
                status=old_status,
                exclude_task_id=task.id,
                lower=old_order,
                upper=None,
                lower_inclusive=False,
                upper_inclusive=False,
                delta=-1,
            )
            self._shift_column(
                project_id=task.project_id,
                status=new_status,
                exclude_task_id=task.id,
                lower=new_order,
                upper=None,
                lower_inclusive=True,
                upper_inclusive=False,
                delta=1,
            )

        task.status = new_status
        task.column_order = new_order

        self.db.commit()
        self.db.refresh(task)

        return task

    def _shift_column(
        self,
        *,
        project_id: int,
        status: str,
        exclude_task_id: int,
        lower: int | None,
        upper: int | None,
        lower_inclusive: bool,
        upper_inclusive: bool,
        delta: int,
    ) -> None:
        query = self.db.query(Task).filter(
            Task.project_id == project_id,
            Task.status == status,
            Task.id != exclude_task_id,
        )

        if lower is not None:
            query = query.filter(
                Task.column_order >= lower if lower_inclusive else Task.column_order > lower
            )

        if upper is not None:
            query = query.filter(
                Task.column_order <= upper if upper_inclusive else Task.column_order < upper
            )

        query.update(
            {Task.column_order: Task.column_order + delta}, synchronize_session=False
        )
