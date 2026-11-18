# Sprint III Document — Automated Lecture Summarization

**Project:** Remote Classroom — Bandwidth-Adaptive Learning Platform for Rural Colleges  
**Team:** Tech Fusion · **Project ID:** PIET/CS/2023-27/05  
**Approved PS:** PIET/CS/FYP/PS-096 · **Guide:** Mr. Indra Kishor · **Section:** 7CSD

## Sprint objective

Add the automated lecture-summary module to the lecture workflow. Audio from a faculty-uploaded recording is converted into text using Speech-to-Text, then the transcript is condensed through an extractive NLP method. The summary is shown beneath the related lecture so students can use Lite Mode when video streaming is difficult.

## Processing flow

```text
Faculty uploads lecture video
          |
          v
Lecture file stored + database record created
          |
          +---------------------> FFmpeg HLS processing (Sprint II)
          |
          v
Background transcription task
          |
          v
OpenAI Whisper — speech to text
          |
          v
Transcript stored against lecture
          |
          v
Sumy TextRank extractive summarizer
          |
          v
Approximately 300–500 word summary
          |
          v
Lite Mode displays summary and full transcript
```

## Planned implementation details

### 1. Audio/transcription

- Use the uploaded lecture recording as input.
- Use FFmpeg/Whisper-compatible audio decoding.
- Run OpenAI Whisper in a background worker rather than in the upload request.
- Store the full transcript and detected language.
- Keep a clear processing status and an error message if speech is not detected or processing fails.

### 2. Text summarization

- Use the Sumy library's TextRank summarizer as the baseline.
- Select important sentences from the transcript rather than creating new content.
- Keep the selected sentences in their original order for readability.
- Target approximately 300–500 words when the transcript is long enough.
- If the lecture transcript itself is shorter than 300 words, return the available extractive text instead of adding unsupported sentences.
- Abstractive transformer-based summarization can be considered as a future improvement; it is not required for this sprint.

### 3. User interface

- Display summary-generation status.
- Show the summary word count.
- Provide a Lite Mode summary view.
- Provide access to the complete transcript for review.
- Keep the original video player available independently of the text summary.

## Processing states

| State | Meaning |
|---|---|
| Waiting | Task has been queued but has not started |
| Processing | Worker is transcribing or summarizing the lecture |
| Ready | Transcript and summary are stored and available |
| Failed | Processing stopped; an error message is stored for diagnosis |

## Main implementation components

| Component | Responsibility |
|---|---|
| OpenAI Whisper | Transcribe speech from the lecture recording |
| Sumy TextRank | Select key sentences from the transcript |
| Celery worker | Run the processing job outside the web request |
| Redis | Queue and coordinate background jobs |
| Django API | Return the transcript, summary and processing state |
| React Lite Mode | Present the summary in a readable text layout |

## Review and test checklist

- [ ] Upload a short recording with clear speech.
- [ ] Confirm that the summary job enters Waiting and Processing states.
- [ ] Confirm that Whisper produces a non-empty transcript.
- [ ] Check a sample transcript manually for obvious recognition errors.
- [ ] Confirm that TextRank returns sentences from the transcript and does not invent content.
- [ ] Check summary word count and ensure the 300–500 target is respected when the transcript is long enough.
- [ ] Confirm that a short transcript is not artificially expanded.
- [ ] Confirm that the summary and transcript appear on the correct lecture page.
- [ ] Test failure handling with a video that has no audible speech or an invalid recording.
- [ ] Save screenshots, sample transcript, generated summary, worker logs and actual test results.

## Risks to record

- Regional accents and background noise may reduce transcription accuracy.
- Long lecture recordings can take time to process on a CPU.
- Video uploads and generated HLS files require sufficient cloud storage.
- A summary is only as reliable as the transcript from which it is extracted.

## Sprint boundary

The per-lecture Doubt/Q&A module, final end-to-end integration and deployment are scheduled for Sprint IV. This document covers only the transcription and summary work added in Sprint III.

## Evidence to attach before submission

Use an actual lecture sample and attach the source filename, transcript excerpt, generated summary, word count, worker processing log and a screenshot of Lite Mode. Do not use sample/fabricated output as evidence of a real run.
