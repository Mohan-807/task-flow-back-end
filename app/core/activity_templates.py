STATUS_LABELS = {
    "todo": "To Do",
    "in_progress": "In Progress",
    "testing": "Testing",
    "done": "Done",
}

PRIORITY_LABELS = {
    "critical": "Critical",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
}

_TEMPLATES = {
    "task_created": "<strong>{actor}</strong> created task <strong>{task_title}</strong>",
    "status_changed": "<strong>{actor}</strong> changed status to <strong>{new_status_label}</strong>",
    "priority_changed": "<strong>{actor}</strong> changed priority to <strong>{new_priority_label}</strong>",
    "comment_added": "<strong>{actor}</strong> added a comment",
    "member_added": "<strong>{actor}</strong> added <strong>{member_name}</strong> to the project",
    "member_removed": "<strong>{actor}</strong> removed <strong>{member_name}</strong> from the project",
    "project_created": "<strong>{actor}</strong> created project <strong>{project_name}</strong>",
    "task_assigned": "<strong>{actor}</strong> assigned task to <strong>{assignee_name}</strong>",
    "task_completed": "<strong>{actor}</strong> marked <strong>{task_title}</strong> as done",
    "task_deleted": "<strong>{actor}</strong> deleted task <strong>{task_title}</strong>",
}


def render_activity_message(activity_type: str, **kwargs: str) -> str:
    return _TEMPLATES[activity_type].format(**kwargs)
