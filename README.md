# Hermes public source worker

A schedule-only, public-data worker using the official Hermes native scheduler
in script-only mode on a standard public GitHub-hosted Ubuntu runner.

No model, provider account, browser session, personal records, private inbox,
application, outreach, credentials, artifact storage or cache is used.
No local production job or canonical prospect store is mirrored here.

The worker collects public regulatory news-index links as discovery inputs.
An index capture is **not** a full article read, editorial approval or advice.
Source failures are recorded independently. Nothing is posted or sent.

Only `schedule` events execute. There is no push/manual dispatch trigger.
GitHub concurrency prevents overlapping workers. Hermes schedules a single
one-shot script and its normal external scheduler tick claims the due job.
Execution evidence is retained in the standard workflow log, without artifacts.

This is an intermittent public research worker, not an always-on gateway or
authenticated browser replacement. Standard public runners are documented as
free; larger runners and paid storage are not configured. The worker runs every
six hours after its first automatic native execution was verified successfully.
