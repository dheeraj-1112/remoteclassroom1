# Sprint I Document — Domain Study, Requirements and SRS

**Project:** Remote Classroom — Bandwidth-Adaptive Learning Platform for Rural Colleges  
**Team:** Tech Fusion · **Project ID:** PIET/CS/2023-27/05  
**Approved PS:** PIET/CS/FYP/PS-096 · **Guide:** Mr. Indra Kishor · **Section:** 7CSD

## Sprint objective

Understand the rural-college learning problem, identify what faculty and students need from the platform, settle the first implementation scope and prepare the Software Requirements Specification (SRS).

## Problem identified

Students who rely on unstable or low-speed internet may not be able to stream or download recorded lectures. Connectivity or electricity interruptions may also prevent attendance in live sessions. If the only learning resource is a video, students have no practical alternative when the video cannot be accessed.

## Users considered

- Faculty: upload lectures, organize subject content and share scheduled live-class links.
- Students: enroll in subjects, view recorded lectures, read summaries and receive timetable notifications.
- Administrator: manage faculty accounts and user roles.

## Requirements gathered

1. Web-based access for faculty and students.
2. Subject-wise lecture organization.
3. Recorded lecture upload and later viewing.
4. Adaptive-bitrate video playback with a text-based Lite Mode alternative.
5. Scheduled Meet/Zoom link sharing and notifications.
6. Automatic speech transcription and an extractive summary of approximately 300–500 words.
7. A per-lecture Doubt/Q&A module in the complete project scope, planned for Sprint IV.

## Technical decisions for the first build

| Area | Decision |
|---|---|
| Frontend | React.js |
| Backend | Django REST Framework with Python |
| Database | PostgreSQL |
| Video processing | FFmpeg and HLS |
| Speech recognition | OpenAI Whisper |
| Text summary | TextRank through Sumy |
| Background processing | Celery with Redis |
| File storage | Local media during development; optional AWS S3 for deployment |
| Live-class service | Paste an existing Google Meet or Zoom link and share it with enrolled students |

## Data design prepared

User/Profile, Subject, Enrollment, Lecture, LiveClass and Notification are the core records for Sprints I–III. Question and Answer are reserved for the Sprint IV discussion module.

## Deliverables

- Approved problem statement and proposed solution text.
- User roles and functional requirements.
- Initial SRS (`docs/SRS.md`).
- Selected technology stack and initial data model.
- Acceptance checklist for the Sprint II and III implementation.

## Sprint review checklist

- [ ] Team can explain the rural connectivity problem in its own words.
- [ ] Team can explain why a text summary is useful when video streaming is not possible.
- [ ] Faculty and student roles are agreed.
- [ ] Functional and non-functional requirements have been reviewed with the guide.
- [ ] Stack choices have been confirmed by the guide.
- [ ] Actual sprint dates and review notes have been added.

## Evidence to attach before submission

Add the actual meeting/review date, SRS review notes, approved requirement changes and screenshots of the requirement/design work. This file records the planned Sprint I outputs; it is not proof that a review or approval occurred.
