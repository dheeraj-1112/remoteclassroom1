# API quick reference

Base URL in local development: `http://localhost:8000/api/`  
Authentication: send `Authorization: Token <token>` for authenticated endpoints.  
JSON is used unless an endpoint accepts a multipart video upload.

## Authentication

### Register student
`POST /auth/register/`

```json
{
  "username": "student.one",
  "email": "student@example.com",
  "password": "Use-A-Strong-Password-Here",
  "first_name": "Student",
  "last_name": "One"
}
```

Registration always creates a Student profile. Faculty accounts are made by an administrator.

### Login
`POST /auth/login/`

```json
{"username": "faculty.demo", "password": "DemoOnlyChange123!"}
```

Returns a token and user object. Use the token in later requests.

### Current user / logout
- `GET /auth/me/`
- `POST /auth/logout/`

## Subjects

- `GET /subjects/` — browse available subjects.
- `GET /subjects/mine/` — faculty's own subjects or student's enrolled subjects.
- `POST /subjects/` — faculty creates a subject.
- `POST /subjects/{id}/enroll/` — student enrolls in a subject.

Create subject example:

```json
{"code": "CSE101", "name": "Computer Science", "description": "Recorded lectures and live sessions."}
```

## Lectures

- `GET /lectures/` — lectures visible to the signed-in account.
- `POST /lectures/` — faculty upload using `multipart/form-data`.
- `GET /lectures/{id}/` — lecture details, statuses, HLS URL, transcript and summary.
- `POST /lectures/{id}/regenerate_summary/` — queue a new Whisper/TextRank job.

Multipart upload fields:

| Field | Value |
|---|---|
| `subject` | Subject database ID |
| `title` | Lecture title |
| `topic` | Topic / chapter (optional) |
| `description` | Short description (optional) |
| `video` | MP4, MOV, MKV, WEBM or AVI file |

The upload API returns before the heavy media jobs finish. Poll the lecture detail endpoint to check `hls_status` and `summary_status`. Allowed statuses are `waiting`, `processing`, `ready` and `failed`.

## Live classes and notifications

- `GET /live-classes/` — future or past class sessions visible to the user.
- `POST /live-classes/` — faculty schedules a session for a subject they own.
- `GET /notifications/` — notifications for the signed-in user.
- `POST /notifications/{id}/mark_read/` — mark one notification read.
- `POST /notifications/mark_all_read/` — mark all current user's notifications read.

Create a live class:

```json
{
  "subject": 1,
  "title": "Unit 1 revision",
  "description": "Bring your lecture notes.",
  "starts_at": "2027-01-15T09:30:00+05:30",
  "meeting_url": "https://meet.google.com/your-room-code"
}
```

A notification is created for each student enrolled in the selected subject.

## Dashboard and health

- `GET /dashboard/` — counts for subjects, lectures, summaries, upcoming live classes and unread notifications.
- `GET /health/` — API service health check (no authentication required).

## Access rules

- Students can browse subjects, enroll and then access lectures/live classes for subjects they have joined.
- Students cannot create subjects, upload lectures or schedule live classes.
- Faculty can create subjects and manage lectures/live classes only for subjects assigned to their own account.
- Public registration creates a student profile only.
- Question/Answer routes are not exposed in this Sprint I–III build; they are scheduled for Sprint IV.
