# System Architecture and Data Flow

## High-level architecture

```mermaid
flowchart LR
    U[Student / Faculty Browser] --> R[React Frontend]
    R -->|REST API + token| D[Django REST Framework]
    D <--> P[(PostgreSQL)]
    D -->|save source video| S[(Local Media / AWS S3)]
    D -->|queue processing| Q[(Redis)]
    Q --> C[Celery Worker]
    C -->|transcode variants| F[FFmpeg / HLS]
    C -->|speech recognition| W[OpenAI Whisper]
    W --> T[Lecture Transcript]
    T --> N[Sumy TextRank]
    N -->|summary + status| P
    F -->|HLS playlist + segments| S
    R -->|HLS playback| S
    R -->|summary + transcript| D
```

## Request and processing sequence

```mermaid
sequenceDiagram
    actor Faculty
    participant UI as React UI
    participant API as Django API
    participant DB as PostgreSQL
    participant Queue as Redis / Celery
    participant Worker as Processing Worker
    participant Store as File Storage

    Faculty->>UI: Upload lecture details and video
    UI->>API: POST multipart lecture upload
    API->>Store: Save source recording
    API->>DB: Create Lecture (waiting states)
    API->>Queue: Enqueue HLS and summary tasks
    API-->>UI: Return lecture record
    Queue->>Worker: Execute processing tasks
    Worker->>Store: Read source recording
    Worker->>Worker: FFmpeg creates HLS renditions
    Worker->>Store: Save master playlist and segments
    Worker->>DB: Update HLS status
    Worker->>Worker: Whisper transcribes speech
    Worker->>Worker: Sumy TextRank extracts key sentences
    Worker->>DB: Save transcript, summary and word count
    UI->>API: Poll lecture processing state
    API-->>UI: Return HLS URL, transcript and summary
    Faculty->>UI: Schedule Meet/Zoom class
    UI->>API: POST live-class details
    API->>DB: Save timetable entry
    API->>DB: Create notifications for enrolled students
```

## Database relationships

```mermaid
erDiagram
    USER ||--|| PROFILE : has
    USER ||--o{ SUBJECT : teaches
    USER ||--o{ ENROLLMENT : joins
    SUBJECT ||--o{ ENROLLMENT : has
    SUBJECT ||--o{ LECTURE : contains
    USER ||--o{ LECTURE : uploads
    SUBJECT ||--o{ LIVE_CLASS : schedules
    USER ||--o{ LIVE_CLASS : creates
    USER ||--o{ NOTIFICATION : receives

    USER {
        int id PK
        string username
        string email
    }
    PROFILE {
        int id PK
        int user_id FK
        string role
    }
    SUBJECT {
        int id PK
        string code UK
        string name
        int faculty_id FK
    }
    ENROLLMENT {
        int id PK
        int student_id FK
        int subject_id FK
    }
    LECTURE {
        int id PK
        int subject_id FK
        int faculty_id FK
        string title
        string video
        string hls_master_key
        string hls_status
        text transcript
        text summary
        string summary_status
    }
    LIVE_CLASS {
        int id PK
        int subject_id FK
        int faculty_id FK
        datetime starts_at
        string meeting_url
    }
    NOTIFICATION {
        int id PK
        int user_id FK
        string title
        boolean is_read
    }
```

Question and Answer entities are deliberately not part of this Sprint I–III database baseline. They are planned for Sprint IV.

## Important engineering decisions

1. **Background tasks:** audio transcription and video conversion run in Celery workers. The HTTP upload request only validates and saves the lecture record; it does not wait for model inference or video encoding.
2. **Two separate processing states:** HLS and summary processing are tracked independently. A failed HLS conversion does not erase the uploaded source video or prevent an independent transcript/summary task.
3. **Access control:** public account registration creates a Student. Faculty accounts must be created by the administrator. Students must enroll before the API returns a subject's lectures or live classes.
4. **Data integrity:** PostgreSQL stores application records. Uploaded binaries and derived HLS files use the configured file storage backend.
5. **Lite Mode:** the summary is extractive and derived from the stored transcript. It is not a replacement for reviewing the original recording when exact wording is important.
