# TaskFlow Backend — Implemented Endpoints

Base URL: `/api/v1`. All protected routes require `Authorization: Bearer <access_token>`.

---

## Authentication

### POST /auth/login
```json
// Request
{ "email": "admin@company.io", "password": "secret123" }
```
```json
// 200 Response
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1, "name": "Alex Johnson", "email": "admin@company.io", "role": "admin",
    "avatarUrl": null, "initials": "AJ", "color": "#6366f1", "status": "active",
    "department": "Engineering", "joinedAt": "2026-01-10T00:00:00", "lastActiveAt": "2026-07-05T12:00:00"
  }
}
```

### GET /auth/me
No request body. Response: same `user` object shape as above.

### POST /auth/token/refresh
```json
// Request
{ "refresh_token": "eyJ..." }
```
Response: same shape as `/auth/login` (new `access_token`, `refresh_token`, `user`).

---

## Users

### POST /users (admin only)
```json
// Request
{
  "name": "Jane Smith", "email": "jane@company.io", "password": "securepass123",
  "role": "developer", "status": "active", "department": "Engineering", "color": "#6366f1"
}
```
```json
// 201 Response
{
  "id": 10, "name": "Jane Smith", "email": "jane@company.io", "role": "developer",
  "avatarUrl": null, "initials": "JS", "color": "#6366f1", "status": "active",
  "department": "Engineering", "joinedAt": "2026-07-05T12:00:00", "lastActiveAt": null
}
```

### POST /users/invite (admin, manager)
```json
// Request
{ "name": "Aisha Thompson", "email": "aisha@company.io", "role": "manager" }
```
```json
// 201 Response
{
  "id": 11, "name": "Aisha Thompson", "email": "aisha@company.io", "role": "manager",
  "avatarUrl": null, "initials": "AT", "color": "#14b8a6", "status": "invited",
  "department": null, "joinedAt": "2026-07-05T12:00:00", "lastActiveAt": null,
  "temporaryPassword": "6BkcHodPfqLY"
}
```

### GET /users?search=&role=&status=&page=1&per_page=50
```json
// 200 Response
{
  "data": [ { "id": 1, "name": "...", "email": "...", "role": "...", "...": "..." } ],
  "pagination": { "total": 9, "page": 1, "per_page": 50, "total_pages": 1 }
}
```

### GET /users/{user_id}
Response: single user object (same shape as create response).

### PATCH /users/{user_id}
Admin: any field. Non-admin: only own record, `name`/`email`/`department`/`color` only.
```json
// Request (all fields optional)
{ "name": "Marcus J. Williams", "department": "Product" }
```
Response: updated user object.

### DELETE /users/{user_id} (admin only)
No body. `204 No Content`.

---

## Projects

### POST /projects (admin, manager)
```json
// Request
{
  "name": "New Product Launch", "description": "Q3 launch", "priority": "high",
  "status": "active", "color": "#6366f1", "dueDate": "2026-09-30", "tags": ["marketing"]
}
```
```json
// 201 Response
{
  "id": 7, "name": "New Product Launch", "description": "Q3 launch", "status": "active",
  "priority": "high", "color": "#6366f1", "progress": 0, "startDate": "2026-07-05",
  "dueDate": "2026-09-30", "ownerId": 1, "memberIds": [1], "tags": ["marketing"],
  "tasksCount": { "total": 0, "todo": 0, "inProgress": 0, "testing": 0, "done": 0 },
  "createdAt": "2026-07-05T12:00:00", "updatedAt": "2026-07-05T12:00:00"
}
```

### GET /projects?status=&search=&priority=&page=1&per_page=20
Response: `{ "data": [Project...], "pagination": {...} }` (role/membership-scoped).

### GET /projects/{project_id}
Response: single project object (same shape as create response).

### PATCH /projects/{project_id} (admin, manager)
```json
// Request (all fields optional)
{ "status": "completed", "dueDate": "2026-08-15" }
```
Response: updated project object.

### DELETE /projects/{project_id} (admin, manager)
No body. `204 No Content`. Cascades tasks, comments, activities.

---

## Project Members

### GET /projects/{project_id}/members
```json
// 200 Response
{
  "data": [
    { "id": 1, "name": "Alex Johnson", "email": "...", "role": "admin", "avatarUrl": null,
      "initials": "AJ", "color": "#6366f1", "status": "active", "department": "Engineering", "isOwner": true }
  ]
}
```

### POST /projects/{project_id}/members (admin, manager)
```json
// Request
{ "user_id": 5 }
```
Response: same shape as GET members list.

### DELETE /projects/{project_id}/members/{user_id} (admin, manager)
No body. Response: same shape as GET members list. (400 if target is the owner.)

### PATCH /projects/{project_id}/members/{user_id} (admin, manager)
```json
// Request
{ "role": "developer" }
```
```json
// 200 Response
{ "id": 5, "name": "Jordan Lee", "role": "developer", "updatedAt": "2026-07-05T12:00:00" }
```

---

## Tasks

### GET /projects/{project_id}/tasks?status=&priority=&assignee_id=&search=&page=1&per_page=100
```json
// 200 Response
{
  "data": [
    { "id": 1, "title": "Design homepage", "description": null, "status": "todo",
      "priority": "high", "projectId": 4, "assigneeId": 3, "reporterId": 1,
      "dueDate": null, "tags": [], "commentsCount": 0, "columnOrder": 0,
      "createdAt": "...", "updatedAt": "..." }
  ],
  "pagination": { "total": 3, "page": 1, "per_page": 100, "total_pages": 1 }
}
```

### POST /projects/{project_id}/tasks
```json
// Request
{
  "title": "Implement login page", "description": "...", "status": "todo",
  "priority": "high", "assigneeId": 3, "dueDate": "2026-07-20", "tags": ["frontend"]
}
```
Response `201`: same task shape as list item above.

### GET /tasks/{task_id}
```json
// 200 Response
{
  "id": 1, "title": "Design homepage", "description": null, "status": "in_progress",
  "priority": "high", "projectId": 4, "projectName": "Website Redesign",
  "assigneeId": 3, "assignee": { "id": 3, "name": "Robert Developer", "initials": "RD", "color": "#6366f1", "avatarUrl": null },
  "reporterId": 1, "reporter": { "id": 1, "name": "Test User", "initials": "TU", "color": "#6366f1", "avatarUrl": null },
  "dueDate": null, "tags": [], "commentsCount": 2, "columnOrder": 0,
  "createdAt": "...", "updatedAt": "..."
}
```

### PATCH /tasks/{task_id}
Admin/manager/tester: any task. Developer: only if assignee or reporter.
```json
// Request (all fields optional)
{ "title": "Design homepage v2", "tags": ["design", "ui"] }
```
Response: same shape as GET task detail.

### DELETE /tasks/{task_id}
Same permission rule as PATCH. `204 No Content`.

### PATCH /tasks/{task_id}/status
```json
// Request
{ "status": "testing" }
```
```json
// 200 Response
{ "id": 1, "status": "testing", "updatedAt": "2026-07-05T12:00:00" }
```

### PATCH /tasks/{task_id}/priority
```json
// Request
{ "priority": "critical" }
```
```json
// 200 Response
{ "id": 1, "priority": "critical", "updatedAt": "2026-07-05T12:00:00" }
```

### PATCH /tasks/{task_id}/assignee (admin, manager)
```json
// Request (send null to unassign)
{ "assigneeId": 3 }
```
```json
// 200 Response
{ "id": 1, "assigneeId": 3, "assignee": { "id": 3, "name": "...", "initials": "...", "color": "...", "avatarUrl": null }, "updatedAt": "..." }
```

### PATCH /tasks/{task_id}/due-date
```json
// Request (send null to clear)
{ "dueDate": "2026-08-01" }
```
```json
// 200 Response
{ "id": 1, "dueDate": "2026-08-01", "updatedAt": "2026-07-05T12:00:00" }
```

---

## Kanban

### GET /projects/{project_id}/kanban
```json
// 200 Response
{
  "projectId": 4,
  "columns": {
    "todo": { "label": "To Do", "tasks": [ { "id": 1, "title": "...", "status": "todo", "priority": "medium", "assigneeId": 3, "assignee": {...}, "reporterId": 1, "dueDate": null, "tags": [], "commentsCount": 0, "columnOrder": 0 } ] },
    "in_progress": { "label": "In Progress", "tasks": [] },
    "testing": { "label": "Testing", "tasks": [] },
    "done": { "label": "Done", "tasks": [] }
  }
}
```

### PATCH /tasks/{task_id}/move
Same permission rule as task edit; developer cannot move a `done` task to another status.
```json
// Request
{ "status": "in_progress", "columnOrder": 1 }
```
```json
// 200 Response
{ "id": 1, "status": "in_progress", "columnOrder": 1, "updatedAt": "2026-07-05T12:00:00" }
```

### GET /projects/{project_id}/kanban/stats
```json
// 200 Response
{
  "projectId": 4, "total": 24,
  "todo": { "count": 5, "percentage": 21 },
  "in_progress": { "count": 8, "percentage": 33 },
  "testing": { "count": 3, "percentage": 13 },
  "done": { "count": 8, "percentage": 33 },
  "progress": 33
}
```

---

## Comments

### GET /tasks/{task_id}/comments?page=1&per_page=50
```json
// 200 Response
{
  "data": [
    { "id": 1, "taskId": 1, "userId": 1, "author": { "id": 1, "name": "...", "initials": "...", "color": "...", "avatarUrl": null },
      "content": "Looks good.", "isEdited": false, "createdAt": "...", "updatedAt": "..." }
  ],
  "pagination": { "total": 2, "page": 1, "per_page": 50, "total_pages": 1 }
}
```

### POST /tasks/{task_id}/comments
```json
// Request
{ "content": "I'll take a look." }
```
Response `201`: same shape as a single comment above.

### PATCH /comments/{comment_id} (own comments only)
```json
// Request
{ "content": "Updated text." }
```
```json
// 200 Response (no author field)
{ "id": 1, "taskId": 1, "userId": 1, "content": "Updated text.", "isEdited": true, "createdAt": "...", "updatedAt": "..." }
```

### DELETE /comments/{comment_id} (own comments, or admin for any)
No body. `204 No Content`.

---

## Activities

### GET /activities?type=&user_id=&page=1&per_page=20 (admin, manager only)
```json
// 200 Response
{
  "data": [
    { "id": 12, "type": "status_changed", "userId": 4, "user": { "id": 4, "name": "...", "initials": "...", "color": "...", "avatarUrl": null },
      "projectId": 1, "taskId": 1, "message": "<strong>Priya Patel</strong> changed status to <strong>In Progress</strong>", "createdAt": "..." }
  ],
  "pagination": { "total": 85, "page": 1, "per_page": 20, "total_pages": 5 }
}
```

### GET /projects/{project_id}/activities?limit=&page=1&per_page=20
Same item shape as above, paginated. `limit` (max 50) overrides `per_page` when provided.

### GET /tasks/{task_id}/activities?limit=5
```json
// 200 Response
{ "data": [ { "id": 11, "type": "comment_added", "...": "..." } ] }
```

---

## Dashboard

### GET /dashboard/stats
```json
// 200 Response
{ "activeProjects": 5, "totalTasks": 110, "teamMembers": 9, "completionRate": 42 }
```

### GET /dashboard/recent-projects
```json
// 200 Response
{
  "data": [
    { "id": 5, "name": "Customer Portal", "status": "active", "priority": "high", "color": "#8b5cf6",
      "progress": 55, "dueDate": "2026-08-30",
      "tasksCount": { "total": 30, "todo": 8, "inProgress": 7, "testing": 4, "done": 11 },
      "members": [ { "id": 1, "initials": "AJ", "color": "#6366f1", "avatarUrl": null } ],
      "updatedAt": "..." }
  ]
}
```
Exactly 4 items, most recently updated first.

### GET /dashboard/recent-tasks
```json
// 200 Response
{
  "data": [
    { "id": 1, "title": "Design homepage mockup", "projectId": 1, "projectName": "Website Redesign",
      "status": "in_progress", "priority": "high", "dueDate": "2026-07-10", "commentsCount": 3,
      "assigneeId": 4, "assignee": { "id": 4, "name": "...", "initials": "...", "color": "...", "avatarUrl": null },
      "updatedAt": "..." }
  ]
}
```
Exactly 7 items, most recently updated first.

### GET /dashboard/activities
Same item shape as the Activities endpoints. Exactly 8 items, most recent first.

---

## Settings

### PATCH /settings/profile
```json
// Request (all fields optional; color must be one of the 8-color palette)
{ "name": "Alex J. Johnson", "department": "Engineering", "color": "#ec4899" }
```
Response: updated user object (same shape as `GET /users/{id}`).

### PATCH /settings/password
```json
// Request
{ "currentPassword": "admin123", "newPassword": "newSecurePassword456", "confirmPassword": "newSecurePassword456" }
```
```json
// 200 Response
{ "message": "Password changed successfully" }
```

### PATCH /settings/notifications
```json
// Request (all fields optional; unset fields keep their prior value)
{ "taskAssigned": true, "weeklyDigest": false }
```
```json
// 200 Response (full merged preference set)
{ "taskAssigned": true, "taskCompleted": true, "commentAdded": true, "projectCreated": true, "memberAdded": true, "weeklyDigest": false }
```

### PATCH /settings/appearance
```json
// Request (all fields optional)
{ "theme": "dark", "density": "compact" }
```
```json
// 200 Response
{ "theme": "dark", "density": "compact" }
```

---

## Health

### GET /health
```json
// 200 Response
{ "status": "Healthy", "message": "The API is up and running!" }
```
