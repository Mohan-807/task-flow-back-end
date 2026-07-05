from app.models.task import Task

TASK_STATUSES = ("todo", "in_progress", "testing", "done")


def count_by_status(tasks: list[Task]) -> dict[str, int]:
    counts = {status: 0 for status in TASK_STATUSES}
    for task in tasks:
        if task.status in counts:
            counts[task.status] += 1
    return counts
