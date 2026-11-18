# Software Requirements Specification (SRS)

## Project identification

- Project: Remote Classroom — Bandwidth-Adaptive Learning Platform for Rural Colleges
- Project ID: PIET/CS/2023-27/05
- Approved problem statement: PIET/CS/FYP/PS-096 — Remote Classroom for Rural Colleges
- Team: Tech Fusion
- Domain: Machine Learning
- Guide: Mr. Indra Kishor
- Section: 7CSD

## 1. Purpose

The purpose of Remote Classroom is to give rural-college students another way to access lecture content when the internet connection is slow or unstable. The system provides subject-organized recorded lectures, links for scheduled live classes and a text-based Lite Mode summary of uploaded lectures.

## 2. Problem addressed

Students in rural areas may have low bandwidth, intermittent connectivity or electricity interruptions. These conditions can prevent them from streaming or downloading lecture videos and can also cause them to miss a live class. A video-only learning system does not provide a reliable alternative when the video cannot be accessed.

## 3. Project objectives

1. Provide a web-based remote classroom suitable for low-bandwidth use.
2. Allow faculty to upload and organize recorded lectures.
3. Allow students to access recordings later through adaptive-bitrate playback.
4. Provide scheduled Google Meet / Zoom links and notifications.
5. Generate a concise text summary of a lecture using Speech-to-Text and NLP so students can read the key content without streaming the full video.
6. Keep a per-lecture doubt and Q&A area in the full project scope; implementation is scheduled for Sprint IV, after the current Sprint III build.

## 4. User classes

### Faculty
- Sign in using an account created by the project administrator.
- Create subjects and manage their subject records.
- Upload recordings with title, topic and description.
- View the status of adaptive video and summary processing.
- Schedule a live class by entering a Google Meet or Zoom joining link.

### Student
- Register a student account and sign in.
- Browse subjects and enroll.
- View lectures for enrolled subjects.
- Watch the recording using adaptive playback or read Lite Mode summary/transcript.
- See scheduled live sessions and class notifications.
- Use Doubt/Q&A once that module is developed in Sprint IV.

### Project administrator
- Create faculty accounts and manage user roles through Django admin.
- Inspect subjects, enrollments, lecture processing status and notifications.

## 5. Functional requirements for Sprints I–III

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Users can authenticate using username and password. | Must |
| FR-02 | New self-service registrations receive the Student role only. | Must |
| FR-03 | A faculty account can create and manage its own subjects. | Must |
| FR-04 | A student can enroll in a subject. | Must |
| FR-05 | Faculty can upload a lecture recording with subject, title, topic and description. | Must |
| FR-06 | Students can access recordings only for subjects in which they are enrolled. | Must |
| FR-07 | The system generates HLS renditions using FFmpeg and provides an adaptive player with original-video fallback. | Should |
| FR-08 | Faculty can schedule a live class with a Google Meet / Zoom URL and a future date/time. | Must |
| FR-09 | Enrolled students receive an in-app notification when a class is scheduled. | Must |
| FR-10 | An asynchronous worker transcribes uploaded lecture audio using Whisper. | Must |
| FR-11 | The transcript is summarized with extractive TextRank using Sumy. | Must |
| FR-12 | Students can view the summary and full transcript for an accessible lecture. | Must |
| FR-13 | The system records processing status and error details for HLS and summary jobs. | Must |

## 6. Non-functional requirements

- **Accessibility:** Keep the main learning path usable on common desktop and mobile screen sizes.
- **Low-bandwidth use:** Text summary must be available independently of video playback once generated.
- **Reliability:** File upload and speech processing must not depend on a long-lived browser request; tasks run in a worker.
- **Security:** Role checks on faculty actions; students must be enrolled before accessing a lecture; passwords are stored by Django's password hashing system.
- **Maintainability:** Keep API, data models, frontend and audio-processing logic in separate modules.
- **Deployability:** Use environment-based configuration and Docker rather than hard-coded machine paths.
- **Data integrity:** Use relational constraints for enrollment and PostgreSQL as the application database.

## 7. Selected implementation stack

React.js; Python; Django REST Framework; PostgreSQL; local media storage in development with optional AWS S3 storage; FFmpeg/HLS; OpenAI Whisper; Sumy TextRank; Celery; Redis; Docker; Postman.

## 8. Main data entities

- User and Profile: account identity and student/faculty role.
- Subject: subject name, code, description and responsible faculty member.
- Enrollment: mapping between a student and subject; one record per pair.
- Lecture: subject, faculty, source recording, HLS status, transcript, summary and processing statuses.
- LiveClass: subject, faculty, start time and Meet/Zoom URL.
- Notification: user, message, link and read status.
- Question and Answer: planned Sprint IV entities for the lecture discussion module.

## 9. Assumptions and limitations

- A faculty member creates the Google Meet / Zoom meeting separately and pastes the joining URL into Remote Classroom; automatic meeting creation through vendor APIs is not part of Sprints I–III.
- Whisper processing time depends on recording duration, model size and available CPU/GPU resources.
- The first local demo should use a short recording with clear speech.
- The summary is extractive. It selects sentences from the transcript and does not generate new explanations. Abstractive transformer summarization remains a future improvement.
- Offline access is not promised in the current build; Lite Mode reduces data use after the summary has been generated and is available online.

## 10. Acceptance criteria for Sprint III baseline

1. A faculty account can create a subject and upload a supported video file.
2. The upload is stored and a Lecture record is created.
3. The worker can create HLS renditions when FFmpeg is installed; the original upload remains available if HLS processing fails.
4. A student account can enroll and access that subject's lecture, but cannot access another subject's lecture without enrollment.
5. The worker can generate a transcript using Whisper and a TextRank summary using Sumy.
6. The frontend displays processing states, a summary and transcript when ready.
7. A faculty member can schedule a future live class and the enrolled student receives an in-app notification.
8. Backend tests for authentication, enrollment and faculty permissions pass.
