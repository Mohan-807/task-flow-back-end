from datetime import date

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user import User


class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        name: str,
        description: str | None,
        status: str,
        priority: str,
        color: str,
        due_date: date | None,
        tags: list[str],
        owner: User,
    ) -> Project:
        project = Project(
            name=name,
            description=description,
            status=status,
            priority=priority,
            color=color,
            due_date=due_date,
            tags=tags,
            owner_id=owner.id,
        )
        project.members.append(owner)

        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)

        return project

    def get_by_id(self, project_id: int) -> Project | None:
        return self.db.get(Project, project_id)

    def get_filtered(
        self,
        *,
        status: str | None,
        search: str | None,
        priority: str | None,
        page: int,
        per_page: int,
        member_user_id: int | None,
    ) -> tuple[list[Project], int]:
        query = self.db.query(Project)

        # None means "privileged role, see everything"; a real id restricts
        # the result set to projects this specific user is a member of.
        if member_user_id is not None:
            query = query.join(Project.members).filter(User.id == member_user_id)

        if status:
            query = query.filter(Project.status == status)

        if search:
            query = query.filter(Project.name.ilike(f"%{search}%"))

        if priority:
            query = query.filter(Project.priority == priority)

        total = query.count()
        projects = (
            query.order_by(Project.id)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return projects, total

    def update(self, project_id: int, fields: dict) -> Project | None:
        project = self.get_by_id(project_id)
        if not project:
            return None

        for key, value in fields.items():
            setattr(project, key, value)

        self.db.commit()
        self.db.refresh(project)

        return project

    def delete(self, project_id: int) -> Project | None:
        project = self.get_by_id(project_id)
        if not project:
            return None

        self.db.delete(project)
        self.db.commit()

        return project

    def add_member(self, project: Project, user: User) -> Project:
        project.members.append(user)
        self.db.commit()
        self.db.refresh(project)
        return project

    def remove_member(self, project: Project, user: User) -> Project:
        project.members.remove(user)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_all(self) -> list[Project]:
        return self.db.query(Project).all()

    def get_recent(self, member_user_id: int | None, limit: int) -> list[Project]:
        query = self.db.query(Project)

        if member_user_id is not None:
            query = query.join(Project.members).filter(User.id == member_user_id)

        return query.order_by(Project.updated_at.desc()).limit(limit).all()
