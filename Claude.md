# Agent execution guidelines for MARU platform

## Core priorities
Correctness
Verification
Minimal changes
Clarity
Maintainability

## Operating principles
Verify reality first before writing code.
Never assume filesystem state or MariaDB schema.
Read relevant React components and FastAPI routers before editing them.
Distinguish actual observations from assumptions.

## Tech stack constraints
Frontend: React, Tailwind CSS
Backend: Python with FastAPI
Database: MariaDB / MySQL (UzCloud hosting)
Cache: Redis
Do not introduce new dependencies unless necessary.
Prefer the simplest solution that correctly solves the problem.

## Database connection
DB Engine: MariaDB 10.5
DB Name: maruplast
DB User: maruplast
Connection string format: mysql+pymysql://maruplast:PASSWORD@localhost:3306/maruplast

## Execution process
Understand the requested feature from requirements.
Inspect relevant files and database models.
Make the smallest correct change.
Verify expected behavior locally or on test instance.
Ensure backend routes are production-ready for UzCloud deployment.

## Editing rules
Change only what is necessary.
Preserve unrelated behavior and existing public interfaces.
Avoid cosmetic edits and formatting churn.
Do not remove unrelated dead code.
Every modified line should have a direct reason tied to the task.

## Failure handling
If blocked, stop and describe the blocker clearly.
State what information is missing.
Do not fabricate progress or hallucinate implementations.
If a request appears destructive to the database, stop and explain the concern.