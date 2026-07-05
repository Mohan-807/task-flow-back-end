from fastapi import APIRouter

from app.api.dependencies.types import CommentServiceDep, CurrentUserDep
from app.schemas.comment import CommentUpdate, CommentUpdateResponse

router = APIRouter(prefix="/comments", tags=["Comments"])


@router.patch("/{comment_id}", response_model=CommentUpdateResponse)
def update_comment(
    comment_id: int,
    comment: CommentUpdate,
    current_user: CurrentUserDep,
    comment_service: CommentServiceDep,
):
    return comment_service.update_comment(comment_id, comment, current_user)

@router.delete("/{comment_id}", status_code=204)
def delete_comment(
    comment_id: int,
    current_user: CurrentUserDep,
    comment_service: CommentServiceDep,
):
    comment_service.delete_comment(comment_id, current_user)
