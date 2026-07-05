API_V1_PREFIX = "/api/v1"

API_TITLE = "TaskFlow Backend API"

API_DESCRIPTION = "Production-ready Task Management Backend built with FastAPI"

# Matches the exact palette documented in spec section 10.1 (Update Profile
# validation rules) — the only place the spec enumerates it explicitly.
USER_COLOR_PALETTE = (
    "#6366f1",
    "#ec4899",
    "#10b981",
    "#f59e0b",
    "#8b5cf6",
    "#06b6d4",
    "#f97316",
    "#14b8a6",
)

# Spec doesn't state authoritative defaults for a brand-new user (only shows
# one example request/response pair) — weeklyDigest off, everything else on
# is the common "opt-out of noisy digests, opt-in to direct notifications"
# convention.
DEFAULT_NOTIFICATION_PREFERENCES = {
    "taskAssigned": True,
    "taskCompleted": True,
    "commentAdded": True,
    "projectCreated": True,
    "memberAdded": True,
    "weeklyDigest": False,
}

DEFAULT_APPEARANCE_PREFERENCES = {
    "theme": "system",
    "density": "default",
}