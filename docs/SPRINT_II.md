# Sprint II Document — Platform Design and Core Classroom Modules

**Project:** Remote Classroom — Bandwidth-Adaptive Learning Platform for Rural Colleges  
**Team:** Tech Fusion · **Project ID:** PIET/CS/2023-27/05  
**Approved PS:** PIET/CS/FYP/PS-096 · **Guide:** Mr. Indra Kishor · **Section:** 7CSD

## Sprint objective

Design the database and user-interface structure, then build the first usable classroom workflow: subject management, recorded lecture upload/viewing and scheduled live-class links.

## Planned work

### 1. Database and access design

- Store user accounts and role information.
- Store subjects and assign a faculty member to each subject.
- Store student-subject enrollments with a unique constraint.
- Store lecture metadata and the uploaded recording location.
- Store live-class title, subject, date/time and joining URL.
- Store in-app notifications for enrolled students.

### 2. Frontend wireframes and screens

- Sign-in and student registration.
- Faculty/student dashboard.
- Subject list and enrollment.
- Lecture list and upload form.
- Lecture detail with video player.
- Live-class timetable and notifications.

### 3. Recorded lecture module

Faculty upload a lecture with a subject, title, topic and description. The platform saves the video and creates a lecture record. FFmpeg generates HLS renditions at appropriate resolutions. The player uses the master HLS playlist when available and retains the original video as a fallback.

### 4. Live-class module

Faculty create a Meet/Zoom session outside the platform, paste the joining link and schedule it against a subject. Students enrolled in that subject receive an in-app notification and see the class in their Live classes list.

## Main implementation components

| Component | Responsibility |
|---|---|
| React frontend | Faculty/student screens and upload forms |
| Django REST API | Authentication, subjects, enrollment, lectures and timetable |
| PostgreSQL | Persistent application records |
| Django file storage / S3 adapter | Uploaded videos and processed HLS files |
| FFmpeg | HLS playlist and video-segment generation |
| Redis + Celery | Process HLS in the background |

## API routes in the baseline

- `POST /api/auth/register/` — student registration.
- `POST /api/auth/login/` — sign-in and token issue.
- `GET /api/auth/me/` — current account.
- `GET /api/subjects/` — browse subjects.
- `POST /api/subjects/` — faculty creates a subject.
- `POST /api/subjects/{id}/enroll/` — student enrollment.
- `GET /api/subjects/mine/` — subjects assigned/enrolled.
- `GET, POST /api/lectures/` — list and upload lectures (faculty upload only).
- `GET /api/lectures/{id}/` — lecture details for an authorized participant.
- `GET, POST /api/live-classes/` — list and schedule sessions.
- `GET /api/notifications/` — current user's notifications.

## Review and test checklist

- [ ] Faculty account can create a subject.
- [ ] Student can register and enroll.
- [ ] Student cannot create a subject or upload a lecture.
- [ ] Faculty cannot upload to a subject owned by another faculty account.
- [ ] A lecture upload creates a lecture record.
- [ ] HLS status changes and the master playlist is generated for a valid video.
- [ ] Original video remains available if HLS processing fails.
- [ ] A future live class can be scheduled with a valid URL.
- [ ] Only enrolled students receive that subject's in-app notification.
- [ ] Actual screenshots and API test results are saved with the sprint submission.

## Sprint boundary

Speech-to-Text and TextRank summarization are Sprint III work. Per-lecture Doubt/Q&A implementation and full cloud deployment are planned for Sprint IV, not counted as Sprint II completion.

## Evidence to attach before submission

Add the actual database screenshot, approved wireframes, upload/player screenshots, live-class record and notification screenshots, API test output and sprint review notes. Do not tick a checklist item until it has been tested on the team's machine.
