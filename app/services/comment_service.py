import math

from app.models.comment import Comment
from app.models.user import User
from app.repositories.comment_repository import CommentRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.comment import (
    CommentCreate,
    CommentResponse,
    CommentUpdate,
    CommentUpdateResponse,
)
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.user import UserSummary
from app.core.activity_templates import render_activity_message
from app.core.exceptions import (
    CannotDeleteOthersCommentException,
    CannotEditOthersCommentException,
    CommentNotFoundException,
    TaskNotFoundException,
)
from app.repositories.activity_repository import ActivityRepository
from app.services.access_control import check_task_access


class CommentService:
    def __init__(
        self,
        comment_repository: CommentRepository,
        task_repository: TaskRepository,
        activity_repository: ActivityRepository,
    ):
        self.comment_repository = comment_repository
        self.task_repository = task_repository
        self.activity_repository = activity_repository

    def list_comments(
        self,
        task_id: int,
        current_user: User,
        page: int,
        per_page: int,
    ) -> PaginatedResponse[CommentResponse]:
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise TaskNotFoundException()

        check_task_access(task, current_user)

        comments, total = self.comment_repository.get_filtered(
            task_id=task_id, page=page, per_page=per_page
        )

        return PaginatedResponse(
            data=[_to_response(comment) for comment in comments],
            pagination=PaginationMeta(
                total=total,
                page=page,
                per_page=per_page,
                total_pages=math.ceil(total / per_page),
            ),
        )

    def add_comment(
        self,
        task_id: int,
        request: CommentCreate,
        current_user: User,
    ) -> CommentResponse:
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise TaskNotFoundException()

        check_task_access(task, current_user)

        comment = self.comment_repository.create(
            task_id=task_id,
            user_id=current_user.id,
            content=request.content,
        )

        self.activity_repository.create(
            type="comment_added",
            user_id=current_user.id,
            project_id=task.project_id,
            task_id=task_id,
            message=render_activity_message("comment_added", actor=current_user.name),
        )

        return _to_response(comment)

    def update_comment(
        self,
        comment_id: int,
        request: CommentUpdate,
        current_user: User,
    ) -> CommentUpdateResponse:
        comment = self.comment_repository.get_by_id(comment_id)
        if not comment:
            raise CommentNotFoundException()

        if comment.user_id != current_user.id:
            raise CannotEditOthersCommentException()

        updated_comment = self.comment_repository.update(
            comment_id, {"content": request.content, "is_edited": True}
        )

        return CommentUpdateResponse(
            id=updated_comment.id,
            taskId=updated_comment.task_id,
            userId=updated_comment.user_id,
            content=updated_comment.content,
            isEdited=updated_comment.is_edited,
            createdAt=updated_comment.created_at,
            updatedAt=updated_comment.updated_at,
        )

    def delete_comment(self, comment_id: int, current_user: User) -> None:
        comment = self.comment_repository.get_by_id(comment_id)
        if not comment:
            raise CommentNotFoundException()

        if current_user.role != "admin" and comment.user_id != current_user.id:
            raise CannotDeleteOthersCommentException()

        self.comment_repository.delete(comment_id)


def _to_response(comment: Comment) -> CommentResponse:
    return CommentResponse(
        id=comment.id,
        taskId=comment.task_id,
        userId=comment.user_id,
        author=UserSummary.model_validate(comment.author),
        content=comment.content,
        isEdited=comment.is_edited,
        createdAt=comment.created_at,
        updatedAt=comment.updated_at,
    )
