# TaskFlow — Backend API Specification

> Generated from the React 19 frontend codebase.  
> Base URL: `https://api.taskflow.io/api/v1`  
> All endpoints return `application/json`.  
> All timestamps are ISO 8601 UTC strings.

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Users](#2-users)
3. [Projects](#3-projects)
4. [Project Members](#4-project-members)
5. [Tasks](#5-tasks)
6. [Kanban](#6-kanban)
7. [Comments](#7-comments)
8. [Dashboard](#8-dashboard)
9. [Activities](#9-activities)
10. [Settings](#10-settings)
11. [API Implementation Order](#api-implementation-order)

---

## Global Conventions

### Request Headers

| Header | Value | Required |
|---|---|---|
| `Authorization` | `Bearer <access_token>` | Yes (all protected routes) |
| `Content-Type` | `application/json` | Yes (POST/PATCH requests) |

### Standard Error Response Shape

```json
{
  "detail": "Human-readable error message"
}
```

### Validation Error Shape (422)

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Enumerations

| Enum | Values |
|---|---|
| `role` | `admin`, `manager`, `developer`, `tester` |
| `user_status` | `active`, `inactive`, `invited` |
| `project_status` | `active`, `completed` |
| `priority` | `critical`, `high`, `medium`, `low` |
| `task_status` | `todo`, `in_progress`, `testing`, `done` |
| `activity_type` | `task_created`, `status_changed`, `priority_changed`, `comment_added`, `member_added`, `member_removed`, `project_created`, `task_assigned`, `task_completed`, `task_deleted` |

---

# 1. Authentication

---

## 1.1 Login

### Purpose
Authenticate a user with email and password. Returns access and refresh tokens along with the authenticated user object.

### HTTP Method
`POST`

### Endpoint
`/auth/login`

### Authentication
Public

### Allowed Roles
All (pre-authentication)

### Path Parameters
None

### Query Parameters
None

### Request Body

```json
{
  "email": "alex@company.io",
  "password": "admin123"
}
```

### Success Response
**Status:** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "user_001",
    "name": "Alex Johnson",
    "email": "alex@company.io",
    "role": "admin",
    "avatarUrl": null,
    "initials": "AJ",
    "color": "#6366f1",
    "status": "active",
    "department": "Engineering",
    "projectIds": ["proj_001", "proj_002", "proj_003", "proj_005"],
    "joinedAt": "2025-01-10T00:00:00Z",
    "lastActiveAt": "2026-06-27T11:00:00Z"
  }
}
```

### Error Responses

**401 Unauthorized** — Invalid credentials
```json
{ "detail": "Invalid email or password" }
```

**403 Forbidden** — Account deactivated
```json
{ "detail": "Your account is inactive. Contact an administrator." }
```

**422 Unprocessable Entity** — Validation failure
```json
{
  "detail": [
    { "loc": ["body", "email"], "msg": "field required", "type": "value_error.missing" }
  ]
}
```

### Validation Rules
- `email`: required, valid email format
- `password`: required, non-empty string

### Notes
- Update `lastActiveAt` on the user record upon successful login.
- Accounts with `status = invited` may log in; do not block them — they are valid sessions.
- Accounts with `status = inactive` must be blocked (403).
- The access token JWT payload must include: `sub` (user_id), `role`, `exp`.

---

## 1.2 Logout

### Purpose
Invalidate the current session by blacklisting the access token and clearing the refresh token.

### HTTP Method
`POST`

### Endpoint
`/auth/logout`

### Authentication
Required

### Allowed Roles
`admin`, `manager`, `developer`, `tester`

### Path Parameters
None

### Query Parameters
None

### Request Body
None

### Success Response
**Status:** `204 No Content`

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

### Notes
- Add the access token to a server-side blacklist (Redis or DB table) until it expires.
- Clear the refresh token record from the database.

---

## 1.3 Get Current User

### Purpose
Return the full profile of the currently authenticated user. Used on app initialization to restore session state.

### HTTP Method
`GET`

### Endpoint
`/auth/me`

### Authentication
Required

### Allowed Roles
`admin`, `manager`, `developer`, `tester`

### Path Parameters
None

### Query Parameters
None

### Request Body
None

### Success Response
**Status:** `200 OK`

```json
{
  "id": "user_001",
  "name": "Alex Johnson",
  "email": "alex@company.io",
  "role": "admin",
  "avatarUrl": null,
  "initials": "AJ",
  "color": "#6366f1",
  "status": "active",
  "department": "Engineering",
  "projectIds": ["proj_001", "proj_002", "proj_003", "proj_005"],
  "joinedAt": "2025-01-10T00:00:00Z",
  "lastActiveAt": "2026-06-27T11:00:00Z"
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

### Notes
- Update `lastActiveAt` on each successful call.

---

## 1.4 Refresh Access Token

### Purpose
Exchange a valid refresh token for a new access token without re-authentication.

### HTTP Method
`POST`

### Endpoint
`/auth/token/refresh`

### Authentication
Public (refresh token is the credential)

### Allowed Roles
All (via refresh token)

### Path Parameters
None

### Query Parameters
None

### Request Body

```json
{
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4..."
}
```

### Success Response
**Status:** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Error Responses

**401 Unauthorized** — Expired or invalid refresh token
```json
{ "detail": "Invalid or expired refresh token" }
```

### Notes
- Implement refresh token rotation: invalidate the used refresh token and issue a new one.
- Store refresh tokens server-side (DB or Redis) for revocation support.

---

# 2. Users

---

## 2.1 List Users

### Purpose
Return a paginated, filterable list of all users. Used by the admin User Management page, the Member picker in TaskDrawer, and the Add Member modal in Project Members.

### HTTP Method
`GET`

### Endpoint
`/users`

### Authentication
Required

### Allowed Roles
`admin`, `manager`, `developer`, `tester`

> **Note:** All authenticated roles can fetch the user list (needed for assignee picker and member search). The admin-exclusive **User Management** page (`/users` route) is enforced on the frontend; the backend returns the same data to all authenticated users.

### Path Parameters
None

### Query Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `search` | string | No | Filter by name or email (case-insensitive, partial match) |
| `role` | string | No | Filter by role: `admin`, `manager`, `developer`, `tester` |
| `status` | string | No | Filter by status: `active`, `inactive`, `invited` |
| `page` | integer | No | Page number (default: 1) |
| `per_page` | integer | No | Items per page (default: 50, max: 100) |

### Request Body
None

### Success Response
**Status:** `200 OK`

```json
{
  "data": [
    {
      "id": "user_001",
      "name": "Alex Johnson",
      "email": "alex@company.io",
      "role": "admin",
      "avatarUrl": null,
      "initials": "AJ",
      "color": "#6366f1",
      "status": "active",
      "department": "Engineering",
      "projectIds": ["proj_001", "proj_002", "proj_003", "proj_005"],
      "joinedAt": "2025-01-10T00:00:00Z",
      "lastActiveAt": "2026-06-27T11:00:00Z"
    }
  ],
  "pagination": {
    "total": 9,
    "page": 1,
    "per_page": 50,
    "total_pages": 1
  }
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

---

## 2.2 Create User

### Purpose
Create a new user account directly (admin only). Used on the User Management page.

### HTTP Method
`POST`

### Endpoint
`/users`

### Authentication
Required

### Allowed Roles
`admin`

### Path Parameters
None

### Query Parameters
None

### Request Body

```json
{
  "name": "Jane Smith",
  "email": "jane@company.io",
  "password": "securepassword123",
  "role": "developer",
  "status": "active",
  "department": "Engineering",
  "color": "#6366f1"
}
```

### Success Response
**Status:** `201 Created`

```json
{
  "id": "user_010",
  "name": "Jane Smith",
  "email": "jane@company.io",
  "role": "developer",
  "avatarUrl": null,
  "initials": "JS",
  "color": "#6366f1",
  "status": "active",
  "department": "Engineering",
  "projectIds": [],
  "joinedAt": "2026-06-27T12:00:00Z",
  "lastActiveAt": null
}
```

### Error Responses

**400 Bad Request** — Email already exists
```json
{ "detail": "A user with this email already exists" }
```

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden**
```json
{ "detail": "Insufficient permissions" }
```

**422 Unprocessable Entity**
```json
{
  "detail": [
    { "loc": ["body", "email"], "msg": "value is not a valid email address", "type": "value_error.email" }
  ]
}
```

### Validation Rules
- `name`: required, 1–100 characters
- `email`: required, valid email format, unique across all users
- `password`: required, minimum 6 characters
- `role`: required, one of `admin`, `manager`, `developer`, `tester`
- `status`: optional, one of `active`, `inactive`, `invited`; defaults to `active`
- `department`: optional, 0–100 characters
- `color`: optional, valid hex color string; server picks a default from the 8-color palette if omitted

### Notes
- Auto-generate `initials` from the first letter of each word in `name` (max 2 characters, uppercase).
- Hash the password with bcrypt before storing.
- `password` must never be returned in any response.

---

## 2.3 Get User by ID

### Purpose
Return a single user's full profile. Used in profile views and member detail lookups.

### HTTP Method
`GET`

### Endpoint
`/users/{user_id}`

### Authentication
Required

### Allowed Roles
`admin`, `manager`, `developer`, `tester`

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `user_id` | string | Yes | Unique user identifier |

### Query Parameters
None

### Request Body
None

### Success Response
**Status:** `200 OK`

```json
{
  "id": "user_003",
  "name": "Marcus Williams",
  "email": "marcus@company.io",
  "role": "developer",
  "avatarUrl": null,
  "initials": "MW",
  "color": "#10b981",
  "status": "active",
  "department": "Engineering",
  "projectIds": ["proj_002", "proj_003"],
  "joinedAt": "2025-03-01T00:00:00Z",
  "lastActiveAt": "2026-06-26T17:45:00Z"
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**404 Not Found**
```json
{ "detail": "User not found" }
```

---

## 2.4 Update User

### Purpose
Partially update a user record. Admin can update any user (role, status, department, name, email). A non-admin user can update only their own `name`, `email`, `department`, and `color`.

### HTTP Method
`PATCH`

### Endpoint
`/users/{user_id}`

### Authentication
Required

### Allowed Roles
`admin` (any user) — `manager`, `developer`, `tester` (own record only, restricted fields)

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `user_id` | string | Yes | Unique user identifier |

### Query Parameters
None

### Request Body

```json
{
  "name": "Marcus J. Williams",
  "email": "marcus.w@company.io",
  "role": "manager",
  "status": "inactive",
  "department": "Product",
  "color": "#8b5cf6"
}
```

> All fields are optional. Send only the fields to update.

### Success Response
**Status:** `200 OK`

```json
{
  "id": "user_003",
  "name": "Marcus J. Williams",
  "email": "marcus.w@company.io",
  "role": "manager",
  "avatarUrl": null,
  "initials": "MJ",
  "color": "#8b5cf6",
  "status": "inactive",
  "department": "Product",
  "projectIds": ["proj_002", "proj_003"],
  "joinedAt": "2025-03-01T00:00:00Z",
  "lastActiveAt": "2026-06-26T17:45:00Z"
}
```

### Error Responses

**400 Bad Request** — Email conflict
```json
{ "detail": "A user with this email already exists" }
```

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden** — Non-admin trying to update another user, or attempting to change own role/status
```json
{ "detail": "Insufficient permissions" }
```

**404 Not Found**
```json
{ "detail": "User not found" }
```

### Validation Rules
- `name`: 1–100 characters
- `email`: valid email format, unique
- `role`: one of `admin`, `manager`, `developer`, `tester`; admin-only field
- `status`: one of `active`, `inactive`, `invited`; admin-only field
- `department`: 0–100 characters
- `color`: valid hex color string
- Re-compute `initials` automatically if `name` changes.

---

## 2.5 Delete User

### Purpose
Permanently delete a user account. Admin only. Used on the User Management page.

### HTTP Method
`DELETE`

### Endpoint
`/users/{user_id}`

### Authentication
Required

### Allowed Roles
`admin`

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `user_id` | string | Yes | Unique user identifier |

### Query Parameters
None

### Request Body
None

### Success Response
**Status:** `204 No Content`

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden**
```json
{ "detail": "Insufficient permissions" }
```

**403 Forbidden** — Cannot delete self
```json
{ "detail": "You cannot delete your own account" }
```

**404 Not Found**
```json
{ "detail": "User not found" }
```

### Notes
- Cascade: remove `user_id` from `memberIds` in all projects the user belongs to.
- Update `projectIds` on the deleted user record (not strictly necessary but keeps data consistent).
- Do **not** cascade-delete tasks or comments — preserve audit history.
- Nullify `assigneeId` on tasks where this user was the assignee.

---

## 2.6 Invite User

### Purpose
Send an invitation to a new user. Creates the account with `status = invited`. Used on the Members page by admin and manager.

### HTTP Method
`POST`

### Endpoint
`/users/invite`

### Authentication
Required

### Allowed Roles
`admin`, `manager`

### Path Parameters
None

### Query Parameters
None

### Request Body

```json
{
  "name": "Aisha Thompson",
  "email": "aisha@company.io",
  "role": "manager"
}
```

### Success Response
**Status:** `201 Created`

```json
{
  "id": "user_010",
  "name": "Aisha Thompson",
  "email": "aisha@company.io",
  "role": "manager",
  "avatarUrl": null,
  "initials": "AT",
  "color": "#14b8a6",
  "status": "invited",
  "department": null,
  "projectIds": [],
  "joinedAt": "2026-06-27T12:00:00Z",
  "lastActiveAt": null
}
```

### Error Responses

**400 Bad Request** — Email already registered
```json
{ "detail": "A user with this email already exists" }
```

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden** — Manager cannot invite admin
```json
{ "detail": "Managers cannot invite users with the admin role" }
```

**422 Unprocessable Entity**
```json
{
  "detail": [
    { "loc": ["body", "email"], "msg": "value is not a valid email address", "type": "value_error.email" }
  ]
}
```

### Validation Rules
- `name`: required, 1–100 characters
- `email`: required, valid email format, unique
- `role`: required, one of `manager`, `developer`, `tester` (managers cannot invite admins)

### Notes
- Generate a temporary password and send an invitation email.
- The user's `status` is set to `invited` until they log in and set their password.
- Auto-generate `initials` from `name`.

---

# 3. Projects

---

## 3.1 List Projects

### Purpose
Return a list of projects visible to the authenticated user. Admins and managers see all projects; developers and testers see only projects they are members of.

### HTTP Method
`GET`

### Endpoint
`/projects`

### Authentication
Required

### Allowed Roles
`admin`, `manager`, `developer`, `tester`

### Path Parameters
None

### Query Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `status` | string | No | Filter by project status: `active`, `completed` |
| `search` | string | No | Filter by project name (case-insensitive, partial match) |
| `priority` | string | No | Filter by priority: `critical`, `high`, `medium`, `low` |
| `page` | integer | No | Page number (default: 1) |
| `per_page` | integer | No | Items per page (default: 20, max: 100) |

### Request Body
None

### Success Response
**Status:** `200 OK`

```json
{
  "data": [
    {
      "id": "proj_001",
      "name": "Website Redesign",
      "description": "Full overhaul of the company marketing site with a modern design system and improved performance.",
      "status": "active",
      "priority": "high",
      "color": "#6366f1",
      "progress": 65,
      "startDate": "2026-01-15",
      "dueDate": "2026-07-30",
      "ownerId": "user_001",
      "memberIds": ["user_001", "user_002", "user_004", "user_005", "user_009"],
      "tags": ["design", "frontend"],
      "tasksCount": {
        "total": 24,
        "todo": 5,
        "inProgress": 8,
        "testing": 3,
        "done": 8
      },
      "createdAt": "2026-01-10T09:00:00Z",
      "updatedAt": "2026-06-20T14:30:00Z"
    }
  ],
  "pagination": {
    "total": 6,
    "page": 1,
    "per_page": 20,
    "total_pages": 1
  }
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

### Notes
- Role-based visibility is enforced server-side: `admin` and `manager` see all; `developer` and `tester` see only projects where their `user_id` is in `memberIds`.
- `progress` is computed as: `(done / total) * 100`, rounded to the nearest integer. Returns `0` if `total` is 0.

---

## 3.2 Create Project

### Purpose
Create a new project. Used on the Projects page. The creator is automatically set as the owner and first member.

### HTTP Method
`POST`

### Endpoint
`/projects`

### Authentication
Required

### Allowed Roles
`admin`, `manager`

### Path Parameters
None

### Query Parameters
None

### Request Body

```json
{
  "name": "New Product Launch",
  "description": "End-to-end coordination for the Q3 product launch.",
  "priority": "high",
  "status": "active",
  "color": "#6366f1",
  "dueDate": "2026-09-30",
  "tags": ["marketing", "launch"]
}
```

### Success Response
**Status:** `201 Created`

```json
{
  "id": "proj_007",
  "name": "New Product Launch",
  "description": "End-to-end coordination for the Q3 product launch.",
  "status": "active",
  "priority": "high",
  "color": "#6366f1",
  "progress": 0,
  "startDate": "2026-06-27",
  "dueDate": "2026-09-30",
  "ownerId": "user_002",
  "memberIds": ["user_002"],
  "tags": ["marketing", "launch"],
  "tasksCount": {
    "total": 0,
    "todo": 0,
    "inProgress": 0,
    "testing": 0,
    "done": 0
  },
  "createdAt": "2026-06-27T12:00:00Z",
  "updatedAt": "2026-06-27T12:00:00Z"
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden**
```json
{ "detail": "Insufficient permissions" }
```

**422 Unprocessable Entity**
```json
{
  "detail": [
    { "loc": ["body", "name"], "msg": "field required", "type": "value_error.missing" }
  ]
}
```

### Validation Rules
- `name`: required, 1–60 characters
- `description`: optional, 0–500 characters
- `priority`: required, one of `critical`, `high`, `medium`, `low`
- `status`: optional, one of `active`, `completed`; defaults to `active`
- `color`: optional, valid hex color string; defaults to `#6366f1`
- `dueDate`: optional, ISO date string (`YYYY-MM-DD`), must be in the future
- `tags`: optional, array of strings, each tag max 30 characters

### Notes
- Set `startDate` to the current server date.
- Set `ownerId` to the authenticated user's ID.
- Add the creator to `memberIds` automatically.
- Add the creator's `project_id` to their `projectIds` in the users table.
- Log a `project_created` activity.

---

## 3.3 Get Project by ID

### Purpose
Return the full details of a single project. Used on the Project Details page.

### HTTP Method
`GET`

### Endpoint
`/projects/{project_id}`

### Authentication
Required

### Allowed Roles
`admin`, `manager` (all projects), `developer`, `tester` (member projects only)

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `project_id` | string | Yes | Unique project identifier |

### Query Parameters
None

### Request Body
None

### Success Response
**Status:** `200 OK`

```json
{
  "id": "proj_001",
  "name": "Website Redesign",
  "description": "Full overhaul of the company marketing site with a modern design system and improved performance.",
  "status": "active",
  "priority": "high",
  "color": "#6366f1",
  "progress": 65,
  "startDate": "2026-01-15",
  "dueDate": "2026-07-30",
  "ownerId": "user_001",
  "memberIds": ["user_001", "user_002", "user_004", "user_005", "user_009"],
  "tags": ["design", "frontend"],
  "tasksCount": {
    "total": 24,
    "todo": 5,
    "inProgress": 8,
    "testing": 3,
    "done": 8
  },
  "createdAt": "2026-01-10T09:00:00Z",
  "updatedAt": "2026-06-20T14:30:00Z"
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden** — Not a project member
```json
{ "detail": "You do not have access to this project" }
```

**404 Not Found**
```json
{ "detail": "Project not found" }
```

---

## 3.4 Update Project

### Purpose
Partially update a project's metadata (name, description, status, priority, color, dueDate, tags). Used on the Project Settings tab and the Edit Project modal.

### HTTP Method
`PATCH`

### Endpoint
`/projects/{project_id}`

### Authentication
Required

### Allowed Roles
`admin`, `manager`

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `project_id` | string | Yes | Unique project identifier |

### Query Parameters
None

### Request Body

```json
{
  "name": "Website Redesign v2",
  "description": "Updated description.",
  "status": "completed",
  "priority": "medium",
  "color": "#10b981",
  "dueDate": "2026-08-15",
  "tags": ["design", "frontend", "v2"]
}
```

> All fields are optional. Send only the fields to update.

### Success Response
**Status:** `200 OK`

Returns the updated project object (same shape as [3.3](#33-get-project-by-id)).

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden**
```json
{ "detail": "Insufficient permissions" }
```

**404 Not Found**
```json
{ "detail": "Project not found" }
```

### Validation Rules
- `name`: 1–60 characters
- `description`: 0–500 characters
- `status`: one of `active`, `completed`
- `priority`: one of `critical`, `high`, `medium`, `low`
- `color`: valid hex color string
- `dueDate`: ISO date string
- `tags`: array of strings, each max 30 characters

### Notes
- Log a `status_changed` activity if `status` changes.
- Update `updatedAt` on every successful PATCH.

---

## 3.5 Delete Project

### Purpose
Permanently delete a project and all its associated tasks and comments. Used on the Project Settings tab danger zone.

### HTTP Method
`DELETE`

### Endpoint
`/projects/{project_id}`

### Authentication
Required

### Allowed Roles
`admin`, `manager`

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `project_id` | string | Yes | Unique project identifier |

### Query Parameters
None

### Request Body
None

### Success Response
**Status:** `204 No Content`

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden**
```json
{ "detail": "Insufficient permissions" }
```

**404 Not Found**
```json
{ "detail": "Project not found" }
```

### Notes
- Cascade delete all tasks belonging to this project.
- Cascade delete all comments on those tasks.
- Remove `project_id` from `projectIds` for all member users.
- Delete all activities associated with this project.

---

# 4. Project Members

---

## 4.1 List Project Members

### Purpose
Return all members of a project with their full user profiles. Used on the Project Members tab and the Overview tab team section.

### HTTP Method
`GET`

### Endpoint
`/projects/{project_id}/members`

### Authentication
Required

### Allowed Roles
`admin`, `manager` (any project), `developer`, `tester` (member projects only)

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `project_id` | string | Yes | Unique project identifier |

### Query Parameters
None

### Request Body
None

### Success Response
**Status:** `200 OK`

```json
{
  "data": [
    {
      "id": "user_001",
      "name": "Alex Johnson",
      "email": "alex@company.io",
      "role": "admin",
      "avatarUrl": null,
      "initials": "AJ",
      "color": "#6366f1",
      "status": "active",
      "department": "Engineering",
      "isOwner": true
    },
    {
      "id": "user_002",
      "name": "Sarah Chen",
      "email": "sarah@company.io",
      "role": "manager",
      "avatarUrl": null,
      "initials": "SC",
      "color": "#ec4899",
      "status": "active",
      "department": "Product",
      "isOwner": false
    }
  ]
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden**
```json
{ "detail": "You do not have access to this project" }
```

**404 Not Found**
```json
{ "detail": "Project not found" }
```

### Notes
- `isOwner` is `true` for the user whose `id` matches the project's `ownerId`.

---

## 4.2 Add Member to Project

### Purpose
Add an existing user to a project's member list. Used on the Project Members tab "Add Member" modal.

### HTTP Method
`POST`

### Endpoint
`/projects/{project_id}/members`

### Authentication
Required

### Allowed Roles
`admin`, `manager`

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `project_id` | string | Yes | Unique project identifier |

### Query Parameters
None

### Request Body

```json
{
  "user_id": "user_005"
}
```

### Success Response
**Status:** `200 OK`

Returns the updated project member list (same shape as [4.1](#41-list-project-members)).

### Error Responses

**400 Bad Request** — User is already a member
```json
{ "detail": "User is already a member of this project" }
```

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden**
```json
{ "detail": "Insufficient permissions" }
```

**404 Not Found** — Project or user not found
```json
{ "detail": "Project not found" }
```

```json
{ "detail": "User not found" }
```

### Validation Rules
- `user_id`: required, must reference an existing user

### Notes
- Append `user_id` to project `memberIds`.
- Append `project_id` to user's `projectIds`.
- Log a `member_added` activity.

---

## 4.3 Remove Member from Project

### Purpose
Remove a user from a project's member list. Used on the Project Members tab remove button.

### HTTP Method
`DELETE`

### Endpoint
`/projects/{project_id}/members/{user_id}`

### Authentication
Required

### Allowed Roles
`admin`, `manager`

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `project_id` | string | Yes | Unique project identifier |
| `user_id` | string | Yes | ID of the user to remove |

### Query Parameters
None

### Request Body
None

### Success Response
**Status:** `200 OK`

Returns the updated project member list (same shape as [4.1](#41-list-project-members)).

### Error Responses

**400 Bad Request** — Cannot remove project owner
```json
{ "detail": "Cannot remove the project owner from the project" }
```

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden**
```json
{ "detail": "Insufficient permissions" }
```

**404 Not Found**
```json
{ "detail": "Project not found" }
```

```json
{ "detail": "User is not a member of this project" }
```

### Notes
- Remove `user_id` from project `memberIds`.
- Remove `project_id` from user's `projectIds`.
- Log a `member_removed` activity.
- Tasks assigned to the removed user remain assigned — do not auto-reassign.

---

## 4.4 Update Member Role

### Purpose
Change a project member's system-wide role. Used on the Project Members tab role dropdown.

### HTTP Method
`PATCH`

### Endpoint
`/projects/{project_id}/members/{user_id}`

### Authentication
Required

### Allowed Roles
`admin`, `manager`

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `project_id` | string | Yes | Unique project identifier |
| `user_id` | string | Yes | ID of the member to update |

### Query Parameters
None

### Request Body

```json
{
  "role": "developer"
}
```

### Success Response
**Status:** `200 OK`

```json
{
  "id": "user_005",
  "name": "Jordan Lee",
  "role": "developer",
  "updatedAt": "2026-06-27T12:00:00Z"
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden** — Manager cannot assign admin role
```json
{ "detail": "Insufficient permissions to assign this role" }
```

**404 Not Found**
```json
{ "detail": "User is not a member of this project" }
```

### Validation Rules
- `role`: required, one of `admin`, `manager`, `developer`, `tester`

### Notes
- This updates the user's **system-wide** `role` field, not a project-scoped role (the frontend has no project-scoped roles).
- Managers cannot promote a user to `admin`.

---

# 5. Tasks

---

## 5.1 List Tasks for Project

### Purpose
Return all tasks for a given project, optionally filtered. Used to populate the Kanban board, Task lists, and overview stats.

### HTTP Method
`GET`

### Endpoint
`/projects/{project_id}/tasks`

### Authentication
Required

### Allowed Roles
`admin`, `manager` (any project), `developer`, `tester` (member projects only)

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `project_id` | string | Yes | Unique project identifier |

### Query Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `status` | string | No | Filter by status: `todo`, `in_progress`, `testing`, `done` |
| `priority` | string | No | Filter by priority: `critical`, `high`, `medium`, `low` |
| `assignee_id` | string | No | Filter by assigned user ID |
| `search` | string | No | Filter by task title (case-insensitive, partial match) |
| `page` | integer | No | Page number (default: 1) |
| `per_page` | integer | No | Items per page (default: 100, max: 200) |

### Request Body
None

### Success Response
**Status:** `200 OK`

```json
{
  "data": [
    {
      "id": "task_001",
      "title": "Design homepage mockup",
      "description": "Create wireframes and high-fidelity mockups for the redesigned homepage.",
      "status": "in_progress",
      "priority": "high",
      "projectId": "proj_001",
      "assigneeId": "user_004",
      "reporterId": "user_001",
      "dueDate": "2026-07-10",
      "tags": ["design", "ui"],
      "commentsCount": 3,
      "columnOrder": 0,
      "createdAt": "2026-01-20T09:00:00Z",
      "updatedAt": "2026-06-15T14:00:00Z"
    }
  ],
  "pagination": {
    "total": 24,
    "page": 1,
    "per_page": 100,
    "total_pages": 1
  }
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden**
```json
{ "detail": "You do not have access to this project" }
```

**404 Not Found**
```json
{ "detail": "Project not found" }
```

### Notes
- Default sort: by `column_order` ascending within each status, then by `created_at` ascending.

---

## 5.2 Create Task

### Purpose
Create a new task in a project. Used from the "Add Task" button in each Kanban column.

### HTTP Method
`POST`

### Endpoint
`/projects/{project_id}/tasks`

### Authentication
Required

### Allowed Roles
`admin`, `manager`, `developer`, `tester`

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `project_id` | string | Yes | Unique project identifier |

### Query Parameters
None

### Request Body

```json
{
  "title": "Implement login page",
  "description": "Build the login form with validation and error states.",
  "status": "todo",
  "priority": "high",
  "assigneeId": "user_003",
  "dueDate": "2026-07-20",
  "tags": ["frontend", "auth"]
}
```

### Success Response
**Status:** `201 Created`

```json
{
  "id": "task_013",
  "title": "Implement login page",
  "description": "Build the login form with validation and error states.",
  "status": "todo",
  "priority": "high",
  "projectId": "proj_001",
  "assigneeId": "user_003",
  "reporterId": "user_002",
  "dueDate": "2026-07-20",
  "tags": ["frontend", "auth"],
  "commentsCount": 0,
  "columnOrder": 5,
  "createdAt": "2026-06-27T12:00:00Z",
  "updatedAt": "2026-06-27T12:00:00Z"
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden**
```json
{ "detail": "You do not have access to this project" }
```

**404 Not Found**
```json
{ "detail": "Project not found" }
```

### Validation Rules
- `title`: required, 1–200 characters
- `description`: optional, 0–2000 characters
- `status`: optional, one of `todo`, `in_progress`, `testing`, `done`; defaults to `todo`
- `priority`: optional, one of `critical`, `high`, `medium`, `low`; defaults to `medium`
- `assigneeId`: optional, must reference a user who is a member of the project
- `dueDate`: optional, ISO date string (`YYYY-MM-DD`)
- `tags`: optional, array of strings, each max 30 characters

### Notes
- Set `reporterId` to the authenticated user's ID.
- Set `columnOrder` to `max(columnOrder) + 1` among tasks with the same `status` in this project (place at bottom of column).
- Recalculate `tasksCount` on the parent project after creation.
- Log a `task_created` activity.
- If `assigneeId` is provided, also log a `task_assigned` activity.

---

## 5.3 Get Task by ID

### Purpose
Return full details of a single task including expanded assignee and reporter user objects. Used by TaskDrawer on open.

### HTTP Method
`GET`

### Endpoint
`/tasks/{task_id}`

### Authentication
Required

### Allowed Roles
`admin`, `manager` (any task), `developer`, `tester` (tasks in member projects only)

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `task_id` | string | Yes | Unique task identifier |

### Query Parameters
None

### Request Body
None

### Success Response
**Status:** `200 OK`

```json
{
  "id": "task_001",
  "title": "Design homepage mockup",
  "description": "Create wireframes and high-fidelity mockups for the redesigned homepage.",
  "status": "in_progress",
  "priority": "high",
  "projectId": "proj_001",
  "projectName": "Website Redesign",
  "assigneeId": "user_004",
  "assignee": {
    "id": "user_004",
    "name": "Priya Patel",
    "initials": "PP",
    "color": "#f59e0b",
    "avatarUrl": null
  },
  "reporterId": "user_001",
  "reporter": {
    "id": "user_001",
    "name": "Alex Johnson",
    "initials": "AJ",
    "color": "#6366f1",
    "avatarUrl": null
  },
  "dueDate": "2026-07-10",
  "tags": ["design", "ui"],
  "commentsCount": 3,
  "columnOrder": 0,
  "createdAt": "2026-01-20T09:00:00Z",
  "updatedAt": "2026-06-15T14:00:00Z"
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden**
```json
{ "detail": "You do not have access to this task" }
```

**404 Not Found**
```json
{ "detail": "Task not found" }
```

---

## 5.4 Update Task

### Purpose
Partially update a task's general fields (title, description, tags). Used from TaskDrawer when editing the task title or description inline.

### HTTP Method
`PATCH`

### Endpoint
`/tasks/{task_id}`

### Authentication
Required

### Allowed Roles
- `admin`, `manager`, `tester`: any task
- `developer`: only tasks where they are the `assigneeId` or `reporterId`

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `task_id` | string | Yes | Unique task identifier |

### Query Parameters
None

### Request Body

```json
{
  "title": "Design homepage mockup v2",
  "description": "Updated description with new requirements.",
  "tags": ["design", "ui", "homepage"]
}
```

> All fields are optional.

### Success Response
**Status:** `200 OK`

Returns the updated task object (same shape as [5.3](#53-get-task-by-id)).

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden**
```json
{ "detail": "You do not have permission to edit this task" }
```

**404 Not Found**
```json
{ "detail": "Task not found" }
```

### Validation Rules
- `title`: 1–200 characters
- `description`: 0–2000 characters
- `tags`: array of strings, each max 30 characters

### Notes
- Update `updatedAt` on the task.

---

## 5.5 Delete Task

### Purpose
Permanently delete a task and its comments. Used from the Delete button in TaskDrawer.

### HTTP Method
`DELETE`

### Endpoint
`/tasks/{task_id}`

### Authentication
Required

### Allowed Roles
- `admin`, `manager`, `tester`: any task
- `developer`: only tasks where they are the `assigneeId` or `reporterId`

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `task_id` | string | Yes | Unique task identifier |

### Query Parameters
None

### Request Body
None

### Success Response
**Status:** `204 No Content`

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden**
```json
{ "detail": "You do not have permission to delete this task" }
```

**404 Not Found**
```json
{ "detail": "Task not found" }
```

### Notes
- Cascade delete all comments on this task.
- Decrement the task count in the parent project's `tasksCount` for the task's status column.
- Recalculate `progress` on the parent project.
- Log a `task_deleted` activity.

---

## 5.6 Update Task Status

### Purpose
Change the status of a task from the status pill selector in TaskDrawer (not a kanban drag-drop; column order is unchanged).

### HTTP Method
`PATCH`

### Endpoint
`/tasks/{task_id}/status`

### Authentication
Required

### Allowed Roles
- `admin`, `manager`, `tester`: any task, any status transition including from `done`
- `developer`: only tasks where they are `assigneeId` or `reporterId`, and **cannot** transition from `done` to another status

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `task_id` | string | Yes | Unique task identifier |

### Query Parameters
None

### Request Body

```json
{
  "status": "testing"
}
```

### Success Response
**Status:** `200 OK`

```json
{
  "id": "task_001",
  "status": "testing",
  "updatedAt": "2026-06-27T12:00:00Z"
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden** — Cannot edit this task
```json
{ "detail": "You do not have permission to edit this task" }
```

**403 Forbidden** — Developer cannot reopen
```json
{ "detail": "You do not have permission to reopen completed tasks" }
```

**404 Not Found**
```json
{ "detail": "Task not found" }
```

### Validation Rules
- `status`: required, one of `todo`, `in_progress`, `testing`, `done`

### Notes
- Recalculate `tasksCount` and `progress` on the parent project.
- If new `status` is `done`, log a `task_completed` activity.
- Otherwise log a `status_changed` activity.
- `developer` permission check: if current `status` is `done` and the new `status` is not `done`, return 403.

---

## 5.7 Update Task Assignee

### Purpose
Assign or unassign a user to a task. Used from the assignee avatar picker in TaskDrawer.

### HTTP Method
`PATCH`

### Endpoint
`/tasks/{task_id}/assignee`

### Authentication
Required

### Allowed Roles
`admin`, `manager`

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `task_id` | string | Yes | Unique task identifier |

### Query Parameters
None

### Request Body

```json
{
  "assigneeId": "user_005"
}
```

> Send `null` for `assigneeId` to unassign the task.

### Success Response
**Status:** `200 OK`

```json
{
  "id": "task_001",
  "assigneeId": "user_005",
  "assignee": {
    "id": "user_005",
    "name": "Jordan Lee",
    "initials": "JL",
    "color": "#8b5cf6",
    "avatarUrl": null
  },
  "updatedAt": "2026-06-27T12:00:00Z"
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden**
```json
{ "detail": "Insufficient permissions" }
```

**404 Not Found**
```json
{ "detail": "Task not found" }
```

**400 Bad Request** — Assignee is not a project member
```json
{ "detail": "The selected user is not a member of this project" }
```

### Validation Rules
- `assigneeId`: must reference an existing user who is a member of the task's project, or `null` to clear

### Notes
- Log a `task_assigned` activity when a new assignee is set.

---

## 5.8 Update Task Priority

### Purpose
Change the priority of a task from the priority pill selector in TaskDrawer.

### HTTP Method
`PATCH`

### Endpoint
`/tasks/{task_id}/priority`

### Authentication
Required

### Allowed Roles
- `admin`, `manager`, `tester`: any task
- `developer`: only tasks where they are `assigneeId` or `reporterId`

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `task_id` | string | Yes | Unique task identifier |

### Query Parameters
None

### Request Body

```json
{
  "priority": "critical"
}
```

### Success Response
**Status:** `200 OK`

```json
{
  "id": "task_001",
  "priority": "critical",
  "updatedAt": "2026-06-27T12:00:00Z"
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden**
```json
{ "detail": "You do not have permission to edit this task" }
```

**404 Not Found**
```json
{ "detail": "Task not found" }
```

### Validation Rules
- `priority`: required, one of `critical`, `high`, `medium`, `low`

### Notes
- Log a `priority_changed` activity.

---

## 5.9 Update Task Due Date

### Purpose
Set or clear the due date on a task from the date picker in TaskDrawer.

### HTTP Method
`PATCH`

### Endpoint
`/tasks/{task_id}/due-date`

### Authentication
Required

### Allowed Roles
- `admin`, `manager`, `tester`: any task
- `developer`: only tasks where they are `assigneeId` or `reporterId`

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `task_id` | string | Yes | Unique task identifier |

### Query Parameters
None

### Request Body

```json
{
  "dueDate": "2026-08-01"
}
```

> Send `null` for `dueDate` to clear it.

### Success Response
**Status:** `200 OK`

```json
{
  "id": "task_001",
  "dueDate": "2026-08-01",
  "updatedAt": "2026-06-27T12:00:00Z"
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden**
```json
{ "detail": "You do not have permission to edit this task" }
```

**404 Not Found**
```json
{ "detail": "Task not found" }
```

### Validation Rules
- `dueDate`: ISO date string (`YYYY-MM-DD`) or `null`

---

# 6. Kanban

---

## 6.1 Get Kanban Board

### Purpose
Return tasks for a project organized into the four Kanban columns, ordered by `columnOrder`. Used when the Board tab is active on the Project Details page.

### HTTP Method
`GET`

### Endpoint
`/projects/{project_id}/kanban`

### Authentication
Required

### Allowed Roles
`admin`, `manager` (any project), `developer`, `tester` (member projects only)

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `project_id` | string | Yes | Unique project identifier |

### Query Parameters
None

### Request Body
None

### Success Response
**Status:** `200 OK`

```json
{
  "projectId": "proj_001",
  "columns": {
    "todo": {
      "label": "To Do",
      "tasks": [
        {
          "id": "task_005",
          "title": "Write unit tests for auth module",
          "status": "todo",
          "priority": "medium",
          "assigneeId": "user_003",
          "assignee": {
            "id": "user_003",
            "name": "Marcus Williams",
            "initials": "MW",
            "color": "#10b981",
            "avatarUrl": null
          },
          "reporterId": "user_001",
          "dueDate": "2026-07-25",
          "tags": ["testing"],
          "commentsCount": 0,
          "columnOrder": 0
        }
      ]
    },
    "in_progress": {
      "label": "In Progress",
      "tasks": []
    },
    "testing": {
      "label": "Testing",
      "tasks": []
    },
    "done": {
      "label": "Done",
      "tasks": []
    }
  }
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden**
```json
{ "detail": "You do not have access to this project" }
```

**404 Not Found**
```json
{ "detail": "Project not found" }
```

### Notes
- Tasks within each column are sorted by `column_order` ascending.
- Each task includes the expanded `assignee` object to avoid N+1 lookups on the frontend.

---

## 6.2 Move Kanban Card

### Purpose
Move a task to a new column (status) and/or reorder it within a column via drag-and-drop. Used by the DnD-Kit drag end handler in KanbanBoard.

### HTTP Method
`PATCH`

### Endpoint
`/tasks/{task_id}/move`

### Authentication
Required

### Allowed Roles
- `admin`, `manager`, `tester`: any task, any status transition
- `developer`: only tasks where they are `assigneeId` or `reporterId`, and **cannot** move from `done` to any other status

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `task_id` | string | Yes | Unique task identifier |

### Query Parameters
None

### Request Body

```json
{
  "status": "in_progress",
  "columnOrder": 1
}
```

### Success Response
**Status:** `200 OK`

```json
{
  "id": "task_005",
  "status": "in_progress",
  "columnOrder": 1,
  "updatedAt": "2026-06-27T12:00:00Z"
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden** — Cannot move this task
```json
{ "detail": "You can only move tasks assigned to or created by you" }
```

**403 Forbidden** — Cannot reopen
```json
{ "detail": "You cannot reopen completed tasks" }
```

**404 Not Found**
```json
{ "detail": "Task not found" }
```

### Validation Rules
- `status`: required, one of `todo`, `in_progress`, `testing`, `done`
- `columnOrder`: required, non-negative integer

### Notes
- After updating the moved task, re-sequence `columnOrder` for all other tasks in the **destination column** to avoid duplicates (shift tasks at or above the new position up by 1).
- If the task moved to a different status column, also compact the `columnOrder` values in the **source column** (close the gap left by the moved task).
- Recalculate `tasksCount` and `progress` on the parent project if status changed.
- If the new status is `done`, log a `task_completed` activity.
- Otherwise log a `status_changed` activity with the new status.
- `developer` reopen check: if old status is `done` and new status is not `done`, return 403.

---

## 6.3 Get Kanban Board Statistics

### Purpose
Return per-column task counts and percentages for a project. Used by the Task Status Overview widget on the Dashboard and Project Overview tab.

### HTTP Method
`GET`

### Endpoint
`/projects/{project_id}/kanban/stats`

### Authentication
Required

### Allowed Roles
`admin`, `manager` (any project), `developer`, `tester` (member projects only)

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `project_id` | string | Yes | Unique project identifier |

### Query Parameters
None

### Request Body
None

### Success Response
**Status:** `200 OK`

```json
{
  "projectId": "proj_001",
  "total": 24,
  "todo":       { "count": 5,  "percentage": 21 },
  "in_progress": { "count": 8,  "percentage": 33 },
  "testing":    { "count": 3,  "percentage": 13 },
  "done":       { "count": 8,  "percentage": 33 },
  "progress": 65
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden**
```json
{ "detail": "You do not have access to this project" }
```

**404 Not Found**
```json
{ "detail": "Project not found" }
```

### Notes
- `progress` = `(done.count / total) * 100`, rounded to nearest integer.
- Percentages are rounded to the nearest integer and may not sum to exactly 100 due to rounding.

---

# 7. Comments

---

## 7.1 List Comments for Task

### Purpose
Return all comments for a task in chronological order. Used in the TaskDrawer comments section.

### HTTP Method
`GET`

### Endpoint
`/tasks/{task_id}/comments`

### Authentication
Required

### Allowed Roles
`admin`, `manager`, `developer`, `tester` (members of the task's project)

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `task_id` | string | Yes | Unique task identifier |

### Query Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `page` | integer | No | Page number (default: 1) |
| `per_page` | integer | No | Items per page (default: 50) |

### Request Body
None

### Success Response
**Status:** `200 OK`

```json
{
  "data": [
    {
      "id": "cmt_001",
      "taskId": "task_001",
      "userId": "user_001",
      "author": {
        "id": "user_001",
        "name": "Alex Johnson",
        "initials": "AJ",
        "color": "#6366f1",
        "avatarUrl": null
      },
      "content": "The wireframes look great. Let's review the mobile breakpoints.",
      "isEdited": false,
      "createdAt": "2026-01-22T10:00:00Z",
      "updatedAt": "2026-01-22T10:00:00Z"
    }
  ],
  "pagination": {
    "total": 3,
    "page": 1,
    "per_page": 50,
    "total_pages": 1
  }
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden**
```json
{ "detail": "You do not have access to this task" }
```

**404 Not Found**
```json
{ "detail": "Task not found" }
```

---

## 7.2 Add Comment

### Purpose
Post a new comment on a task. Used from the comment input box in TaskDrawer.

### HTTP Method
`POST`

### Endpoint
`/tasks/{task_id}/comments`

### Authentication
Required

### Allowed Roles
`admin`, `manager`, `developer`, `tester`

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `task_id` | string | Yes | Unique task identifier |

### Query Parameters
None

### Request Body

```json
{
  "content": "I'll start on the responsive breakpoints today."
}
```

### Success Response
**Status:** `201 Created`

```json
{
  "id": "cmt_009",
  "taskId": "task_001",
  "userId": "user_004",
  "author": {
    "id": "user_004",
    "name": "Priya Patel",
    "initials": "PP",
    "color": "#f59e0b",
    "avatarUrl": null
  },
  "content": "I'll start on the responsive breakpoints today.",
  "isEdited": false,
  "createdAt": "2026-06-27T12:00:00Z",
  "updatedAt": "2026-06-27T12:00:00Z"
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden**
```json
{ "detail": "You do not have access to this task" }
```

**404 Not Found**
```json
{ "detail": "Task not found" }
```

### Validation Rules
- `content`: required, 1–2000 characters

### Notes
- Increment `commentsCount` on the task.
- Log a `comment_added` activity.

---

## 7.3 Update Comment

### Purpose
Edit the content of an existing comment. Users can only edit their own comments.

### HTTP Method
`PATCH`

### Endpoint
`/comments/{comment_id}`

### Authentication
Required

### Allowed Roles
`admin`, `manager`, `developer`, `tester` (own comments only)

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `comment_id` | string | Yes | Unique comment identifier |

### Query Parameters
None

### Request Body

```json
{
  "content": "I'll start on the responsive breakpoints tomorrow instead."
}
```

### Success Response
**Status:** `200 OK`

```json
{
  "id": "cmt_009",
  "taskId": "task_001",
  "userId": "user_004",
  "content": "I'll start on the responsive breakpoints tomorrow instead.",
  "isEdited": true,
  "createdAt": "2026-06-27T12:00:00Z",
  "updatedAt": "2026-06-27T12:30:00Z"
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden** — Not the comment author
```json
{ "detail": "You can only edit your own comments" }
```

**404 Not Found**
```json
{ "detail": "Comment not found" }
```

### Validation Rules
- `content`: required, 1–2000 characters

### Notes
- Set `isEdited = true` and update `updatedAt`.

---

## 7.4 Delete Comment

### Purpose
Delete a comment. Users can delete their own comments. Admin can delete any comment.

### HTTP Method
`DELETE`

### Endpoint
`/comments/{comment_id}`

### Authentication
Required

### Allowed Roles
`admin` (any comment), `manager`, `developer`, `tester` (own comments only)

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `comment_id` | string | Yes | Unique comment identifier |

### Query Parameters
None

### Request Body
None

### Success Response
**Status:** `204 No Content`

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden** — Not the comment author and not admin
```json
{ "detail": "You can only delete your own comments" }
```

**404 Not Found**
```json
{ "detail": "Comment not found" }
```

### Notes
- Decrement `commentsCount` on the parent task.

---

# 8. Dashboard

---

## 8.1 Get Dashboard Statistics

### Purpose
Return aggregate statistics for the authenticated user's dashboard: active projects, total tasks, team members, and completion rate. Used by the four stat cards at the top of the Dashboard page.

### HTTP Method
`GET`

### Endpoint
`/dashboard/stats`

### Authentication
Required

### Allowed Roles
`admin`, `manager`, `developer`, `tester`

### Path Parameters
None

### Query Parameters
None

### Request Body
None

### Success Response
**Status:** `200 OK`

```json
{
  "activeProjects": 5,
  "totalTasks": 110,
  "teamMembers": 9,
  "completionRate": 42
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

### Notes
- `activeProjects`: count of projects with `status = active` visible to the current user.
- `totalTasks`: count of all tasks across all visible projects.
- `teamMembers`: count of all users in the system (regardless of role).
- `completionRate`: `(done_tasks / total_tasks) * 100` across all visible projects, rounded to integer. Returns `0` if no tasks exist.

---

## 8.2 Get Recent Projects

### Purpose
Return the 4 most recently updated projects visible to the user. Used by the Recent Projects section on the Dashboard.

### HTTP Method
`GET`

### Endpoint
`/dashboard/recent-projects`

### Authentication
Required

### Allowed Roles
`admin`, `manager`, `developer`, `tester`

### Path Parameters
None

### Query Parameters
None

### Request Body
None

### Success Response
**Status:** `200 OK`

```json
{
  "data": [
    {
      "id": "proj_005",
      "name": "Customer Portal",
      "status": "active",
      "priority": "high",
      "color": "#8b5cf6",
      "progress": 55,
      "dueDate": "2026-08-30",
      "tasksCount": {
        "total": 30,
        "todo": 8,
        "inProgress": 7,
        "testing": 4,
        "done": 11
      },
      "members": [
        { "id": "user_001", "initials": "AJ", "color": "#6366f1", "avatarUrl": null },
        { "id": "user_004", "initials": "PP", "color": "#f59e0b", "avatarUrl": null },
        { "id": "user_006", "initials": "ER", "color": "#06b6d4", "avatarUrl": null }
      ],
      "updatedAt": "2026-06-24T13:00:00Z"
    }
  ]
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

### Notes
- Return exactly 4 projects, sorted by `updatedAt` descending.
- Each project includes an abbreviated `members` array for avatar rendering.
- Role-based visibility applies (developers/testers see only their projects).

---

## 8.3 Get Recent Tasks

### Purpose
Return the 7 most recently updated tasks across all visible projects. Used by the Recent Tasks table on the Dashboard.

### HTTP Method
`GET`

### Endpoint
`/dashboard/recent-tasks`

### Authentication
Required

### Allowed Roles
`admin`, `manager`, `developer`, `tester`

### Path Parameters
None

### Query Parameters
None

### Request Body
None

### Success Response
**Status:** `200 OK`

```json
{
  "data": [
    {
      "id": "task_001",
      "title": "Design homepage mockup",
      "projectId": "proj_001",
      "projectName": "Website Redesign",
      "status": "in_progress",
      "priority": "high",
      "dueDate": "2026-07-10",
      "commentsCount": 3,
      "assigneeId": "user_004",
      "assignee": {
        "id": "user_004",
        "name": "Priya Patel",
        "initials": "PP",
        "color": "#f59e0b",
        "avatarUrl": null
      },
      "updatedAt": "2026-06-15T14:00:00Z"
    }
  ]
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

### Notes
- Return exactly 7 tasks, sorted by `updatedAt` descending.
- Includes `projectName` to avoid a separate project lookup on the frontend.

---

## 8.4 Get Dashboard Activity Feed

### Purpose
Return the 8 most recent activity events across all visible projects. Used by the Activity Timeline on the Dashboard.

### HTTP Method
`GET`

### Endpoint
`/dashboard/activities`

### Authentication
Required

### Allowed Roles
`admin`, `manager`, `developer`, `tester`

### Path Parameters
None

### Query Parameters
None

### Request Body
None

### Success Response
**Status:** `200 OK`

```json
{
  "data": [
    {
      "id": "act_012",
      "type": "status_changed",
      "userId": "user_004",
      "user": {
        "id": "user_004",
        "name": "Priya Patel",
        "initials": "PP",
        "color": "#f59e0b",
        "avatarUrl": null
      },
      "projectId": "proj_001",
      "taskId": "task_001",
      "message": "<strong>Priya Patel</strong> changed status to <strong>In Progress</strong>",
      "createdAt": "2026-06-27T11:30:00Z"
    }
  ]
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

### Notes
- Return exactly 8 activities, sorted by `createdAt` descending.
- `message` is a pre-rendered HTML string for display with `innerHTML`.
- Role-based visibility: developers/testers see only activities from their projects.

---

# 9. Activities

---

## 9.1 List Global Activities

### Purpose
Return a paginated activity feed across all projects. Used for global audit trail (admin/manager only).

### HTTP Method
`GET`

### Endpoint
`/activities`

### Authentication
Required

### Allowed Roles
`admin`, `manager`

### Path Parameters
None

### Query Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `type` | string | No | Filter by activity type (see activity_type enum) |
| `user_id` | string | No | Filter by actor user ID |
| `page` | integer | No | Page number (default: 1) |
| `per_page` | integer | No | Items per page (default: 20, max: 100) |

### Request Body
None

### Success Response
**Status:** `200 OK`

```json
{
  "data": [
    {
      "id": "act_012",
      "type": "status_changed",
      "userId": "user_004",
      "user": {
        "id": "user_004",
        "name": "Priya Patel",
        "initials": "PP",
        "color": "#f59e0b",
        "avatarUrl": null
      },
      "projectId": "proj_001",
      "taskId": "task_001",
      "message": "<strong>Priya Patel</strong> changed status to <strong>In Progress</strong>",
      "createdAt": "2026-06-27T11:30:00Z"
    }
  ],
  "pagination": {
    "total": 85,
    "page": 1,
    "per_page": 20,
    "total_pages": 5
  }
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden**
```json
{ "detail": "Insufficient permissions" }
```

---

## 9.2 List Project Activities

### Purpose
Return the activity timeline for a specific project. Used on the Project Overview tab "Recent Activity" section and ProjectDetails activity feed.

### HTTP Method
`GET`

### Endpoint
`/projects/{project_id}/activities`

### Authentication
Required

### Allowed Roles
`admin`, `manager` (any project), `developer`, `tester` (member projects only)

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `project_id` | string | Yes | Unique project identifier |

### Query Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `limit` | integer | No | Maximum results to return (default: 6, max: 50) |
| `page` | integer | No | Page number (default: 1) |
| `per_page` | integer | No | Items per page (default: 20) |

### Request Body
None

### Success Response
**Status:** `200 OK`

```json
{
  "data": [
    {
      "id": "act_010",
      "type": "task_created",
      "userId": "user_002",
      "user": {
        "id": "user_002",
        "name": "Sarah Chen",
        "initials": "SC",
        "color": "#ec4899",
        "avatarUrl": null
      },
      "projectId": "proj_001",
      "taskId": "task_012",
      "message": "<strong>Sarah Chen</strong> created task <strong>Set up CI/CD pipeline</strong>",
      "createdAt": "2026-06-20T14:00:00Z"
    }
  ],
  "pagination": {
    "total": 22,
    "page": 1,
    "per_page": 20,
    "total_pages": 2
  }
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden**
```json
{ "detail": "You do not have access to this project" }
```

**404 Not Found**
```json
{ "detail": "Project not found" }
```

---

## 9.3 List Task Activities

### Purpose
Return the activity history for a specific task. Used in the TaskDrawer activity timeline (shows 5 most recent).

### HTTP Method
`GET`

### Endpoint
`/tasks/{task_id}/activities`

### Authentication
Required

### Allowed Roles
`admin`, `manager`, `developer`, `tester` (members of the task's project)

### Path Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `task_id` | string | Yes | Unique task identifier |

### Query Parameters

| Name | Type | Required | Description |
|---|---|---|---|
| `limit` | integer | No | Maximum results to return (default: 5, max: 50) |

### Request Body
None

### Success Response
**Status:** `200 OK`

```json
{
  "data": [
    {
      "id": "act_011",
      "type": "comment_added",
      "userId": "user_001",
      "user": {
        "id": "user_001",
        "name": "Alex Johnson",
        "initials": "AJ",
        "color": "#6366f1",
        "avatarUrl": null
      },
      "projectId": "proj_001",
      "taskId": "task_001",
      "message": "<strong>Alex Johnson</strong> added a comment",
      "createdAt": "2026-01-22T10:00:00Z"
    }
  ]
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden**
```json
{ "detail": "You do not have access to this task" }
```

**404 Not Found**
```json
{ "detail": "Task not found" }
```

---

# 10. Settings

---

## 10.1 Update Profile

### Purpose
Update the authenticated user's own profile: name, email, department, and avatar color. Used on the Settings → Profile tab.

### HTTP Method
`PATCH`

### Endpoint
`/settings/profile`

### Authentication
Required

### Allowed Roles
`admin`, `manager`, `developer`, `tester`

### Path Parameters
None

### Query Parameters
None

### Request Body

```json
{
  "name": "Alex J. Johnson",
  "email": "alex.j@company.io",
  "department": "Engineering",
  "color": "#ec4899"
}
```

> All fields are optional.

### Success Response
**Status:** `200 OK`

```json
{
  "id": "user_001",
  "name": "Alex J. Johnson",
  "email": "alex.j@company.io",
  "role": "admin",
  "avatarUrl": null,
  "initials": "AJ",
  "color": "#ec4899",
  "status": "active",
  "department": "Engineering",
  "projectIds": ["proj_001", "proj_002", "proj_003", "proj_005"],
  "joinedAt": "2025-01-10T00:00:00Z",
  "lastActiveAt": "2026-06-27T12:00:00Z"
}
```

### Error Responses

**400 Bad Request** — Email already in use by another user
```json
{ "detail": "A user with this email already exists" }
```

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

### Validation Rules
- `name`: 1–100 characters
- `email`: valid email format, unique across all users
- `department`: 0–100 characters
- `color`: valid hex color string from the allowed palette: `#6366f1`, `#ec4899`, `#10b981`, `#f59e0b`, `#8b5cf6`, `#06b6d4`, `#f97316`, `#14b8a6`

### Notes
- Re-compute `initials` automatically if `name` changes.
- This is equivalent to `PATCH /users/{user_id}` for the own user — implementations may share the same handler.

---

## 10.2 Change Password

### Purpose
Change the authenticated user's own password. Used on the Settings → Security tab.

### HTTP Method
`PATCH`

### Endpoint
`/settings/password`

### Authentication
Required

### Allowed Roles
`admin`, `manager`, `developer`, `tester`

### Path Parameters
None

### Query Parameters
None

### Request Body

```json
{
  "currentPassword": "admin123",
  "newPassword": "newSecurePassword456",
  "confirmPassword": "newSecurePassword456"
}
```

### Success Response
**Status:** `200 OK`

```json
{
  "message": "Password changed successfully"
}
```

### Error Responses

**400 Bad Request** — Current password incorrect
```json
{ "detail": "Current password is incorrect" }
```

**400 Bad Request** — Passwords do not match
```json
{ "detail": "New password and confirmation do not match" }
```

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

**422 Unprocessable Entity**
```json
{
  "detail": [
    { "loc": ["body", "newPassword"], "msg": "ensure this value has at least 6 characters", "type": "value_error.any_str.min_length" }
  ]
}
```

### Validation Rules
- `currentPassword`: required, must match the user's stored (hashed) password
- `newPassword`: required, minimum 6 characters
- `confirmPassword`: required, must equal `newPassword`

### Notes
- Hash the new password with bcrypt before storing.
- After changing the password, invalidate all existing refresh tokens for this user (force re-login on other devices).

---

## 10.3 Update Notification Preferences

### Purpose
Save the authenticated user's notification toggle preferences. Used on the Settings → Notifications tab.

### HTTP Method
`PATCH`

### Endpoint
`/settings/notifications`

### Authentication
Required

### Allowed Roles
`admin`, `manager`, `developer`, `tester`

### Path Parameters
None

### Query Parameters
None

### Request Body

```json
{
  "taskAssigned": true,
  "taskCompleted": true,
  "commentAdded": true,
  "projectCreated": false,
  "memberAdded": true,
  "weeklyDigest": false
}
```

> All fields are optional. Send only the fields to update.

### Success Response
**Status:** `200 OK`

```json
{
  "taskAssigned": true,
  "taskCompleted": true,
  "commentAdded": true,
  "projectCreated": false,
  "memberAdded": true,
  "weeklyDigest": false
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

### Validation Rules
- All fields: boolean values

---

## 10.4 Update Appearance Preferences

### Purpose
Save the authenticated user's UI appearance preferences (theme and density). Used on the Settings → Appearance tab.

### HTTP Method
`PATCH`

### Endpoint
`/settings/appearance`

### Authentication
Required

### Allowed Roles
`admin`, `manager`, `developer`, `tester`

### Path Parameters
None

### Query Parameters
None

### Request Body

```json
{
  "theme": "dark",
  "density": "compact"
}
```

> All fields are optional.

### Success Response
**Status:** `200 OK`

```json
{
  "theme": "dark",
  "density": "compact"
}
```

### Error Responses

**401 Unauthorized**
```json
{ "detail": "Not authenticated" }
```

### Validation Rules
- `theme`: one of `light`, `dark`, `system`
- `density`: one of `compact`, `default`, `comfortable`

### Notes
- Store these preferences on the `user` record (or a separate `user_preferences` table for cleaner schema design).
- The frontend reads these preferences from the response of `/auth/me` on app initialization.

---

# API Implementation Order

Implement the APIs in this sequence. Each phase depends on the one before it.

---

### Phase 1 — Foundation

| Order | Module | Endpoint | Reason |
|---|---|---|---|
| 1 | Authentication | `POST /auth/login` | Gate everything else |
| 2 | Authentication | `GET /auth/me` | App init / session restore |
| 3 | Authentication | `POST /auth/logout` | Secure session termination |
| 4 | Authentication | `POST /auth/token/refresh` | Token lifecycle management |

---

### Phase 2 — Users

| Order | Module | Endpoint | Reason |
|---|---|---|---|
| 5 | Users | `GET /users` | Required by all pickers and member lists |
| 6 | Users | `POST /users` | Admin user creation |
| 7 | Users | `GET /users/{user_id}` | Profile lookup |
| 8 | Users | `PATCH /users/{user_id}` | Admin edit / self-profile |
| 9 | Users | `DELETE /users/{user_id}` | Admin user removal |
| 10 | Users | `POST /users/invite` | Member invitation flow |

---

### Phase 3 — Projects

| Order | Module | Endpoint | Reason |
|---|---|---|---|
| 11 | Projects | `GET /projects` | Projects listing page |
| 12 | Projects | `POST /projects` | Create project |
| 13 | Projects | `GET /projects/{project_id}` | Project Details page |
| 14 | Projects | `PATCH /projects/{project_id}` | Edit project |
| 15 | Projects | `DELETE /projects/{project_id}` | Delete project |

---

### Phase 4 — Project Members

| Order | Module | Endpoint | Reason |
|---|---|---|---|
| 16 | Project Members | `GET /projects/{project_id}/members` | Members tab |
| 17 | Project Members | `POST /projects/{project_id}/members` | Add member |
| 18 | Project Members | `DELETE /projects/{project_id}/members/{user_id}` | Remove member |
| 19 | Project Members | `PATCH /projects/{project_id}/members/{user_id}` | Change member role |

---

### Phase 5 — Tasks

| Order | Module | Endpoint | Reason |
|---|---|---|---|
| 20 | Tasks | `GET /projects/{project_id}/tasks` | Task lists, kanban data |
| 21 | Tasks | `POST /projects/{project_id}/tasks` | Create task |
| 22 | Tasks | `GET /tasks/{task_id}` | TaskDrawer open |
| 23 | Tasks | `PATCH /tasks/{task_id}` | Edit title / description |
| 24 | Tasks | `PATCH /tasks/{task_id}/status` | Status pill change |
| 25 | Tasks | `PATCH /tasks/{task_id}/priority` | Priority pill change |
| 26 | Tasks | `PATCH /tasks/{task_id}/assignee` | Assignee picker |
| 27 | Tasks | `PATCH /tasks/{task_id}/due-date` | Date picker |
| 28 | Tasks | `DELETE /tasks/{task_id}` | Delete task |

---

### Phase 6 — Kanban

| Order | Module | Endpoint | Reason |
|---|---|---|---|
| 29 | Kanban | `GET /projects/{project_id}/kanban` | Board tab |
| 30 | Kanban | `PATCH /tasks/{task_id}/move` | Drag-and-drop |
| 31 | Kanban | `GET /projects/{project_id}/kanban/stats` | Stats widget |

---

### Phase 7 — Comments

| Order | Module | Endpoint | Reason |
|---|---|---|---|
| 32 | Comments | `GET /tasks/{task_id}/comments` | TaskDrawer comments |
| 33 | Comments | `POST /tasks/{task_id}/comments` | Add comment |
| 34 | Comments | `PATCH /comments/{comment_id}` | Edit own comment |
| 35 | Comments | `DELETE /comments/{comment_id}` | Delete comment |

---

### Phase 8 — Dashboard

| Order | Module | Endpoint | Reason |
|---|---|---|---|
| 36 | Dashboard | `GET /dashboard/stats` | Stat cards |
| 37 | Dashboard | `GET /dashboard/recent-projects` | Recent projects widget |
| 38 | Dashboard | `GET /dashboard/recent-tasks` | Recent tasks widget |
| 39 | Dashboard | `GET /dashboard/activities` | Activity timeline |

---

### Phase 9 — Activities

| Order | Module | Endpoint | Reason |
|---|---|---|---|
| 40 | Activities | `GET /projects/{project_id}/activities` | Project Overview tab |
| 41 | Activities | `GET /tasks/{task_id}/activities` | TaskDrawer history |
| 42 | Activities | `GET /activities` | Global audit log |

---

### Phase 10 — Settings

| Order | Module | Endpoint | Reason |
|---|---|---|---|
| 43 | Settings | `PATCH /settings/profile` | Profile tab |
| 44 | Settings | `PATCH /settings/password` | Security tab |
| 45 | Settings | `PATCH /settings/notifications` | Notifications tab |
| 46 | Settings | `PATCH /settings/appearance` | Appearance tab |

---

**Total: 46 endpoints across 10 modules.**

---

## Appendix — Activity Message Templates

The backend generates HTML activity messages for display in the frontend. Use these templates:

| Type | Template |
|---|---|
| `task_created` | `<strong>{actor}</strong> created task <strong>{task_title}</strong>` |
| `status_changed` | `<strong>{actor}</strong> changed status to <strong>{new_status_label}</strong>` |
| `priority_changed` | `<strong>{actor}</strong> changed priority to <strong>{new_priority_label}</strong>` |
| `comment_added` | `<strong>{actor}</strong> added a comment` |
| `member_added` | `<strong>{actor}</strong> added <strong>{member_name}</strong> to the project` |
| `member_removed` | `<strong>{actor}</strong> removed <strong>{member_name}</strong> from the project` |
| `project_created` | `<strong>{actor}</strong> created project <strong>{project_name}</strong>` |
| `task_assigned` | `<strong>{actor}</strong> assigned task to <strong>{assignee_name}</strong>` |
| `task_completed` | `<strong>{actor}</strong> marked <strong>{task_title}</strong> as done` |
| `task_deleted` | `<strong>{actor}</strong> deleted task <strong>{task_title}</strong>` |

**Status label map:** `todo` → `To Do`, `in_progress` → `In Progress`, `testing` → `Testing`, `done` → `Done`  
**Priority label map:** `critical` → `Critical`, `high` → `High`, `medium` → `Medium`, `low` → `Low`
