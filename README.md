# Canvas Course Creator

A Python script that copies all quizzes (including questions) from one Canvas LMS course to another.

## What it does

Given a source course ID and a target course ID, it fetches every quiz from the source course via the Canvas API and recreates them in the target course — including all questions, answer options, and settings (time limit, shuffle answers, scoring policy, etc.).

Supports question types including multiple choice, true/false, and matching questions.

## Files

- `copy_quizzes_final.py` — the main script to use
- `copy_quizzes.py` — earlier version
- `debug_matching_question.py` — dumps raw JSON for a matching question, useful when Canvas's API shape needs re-checking
- `debug_answer_comments_scan.py` — scans a course for per-answer comments that can't be copied (see below), independent of a copy run
- `debug_migration_issues.py` / `debug_migration_detail.py` — inspect a course's content_migrations history and logged issues (useful for diagnosing why a native Canvas course copy dropped content)
- `debug_diff_quizzes.py` — diffs quiz titles between a source and target course to see exactly what's missing
- `native_copy_quizzes.py` — triggers a real, targeted Canvas content migration (`select[quizzes]`) instead of reconstructing questions via the API. **Currently non-functional on this account** - see "Why this script exists" below - kept in case Instructure ever fixes the underlying bug, since native copy would have full fidelity (including per-answer comments, which `copy_quizzes_final.py` cannot copy).

## Usage

```bash
pip install requests
python copy_quizzes_final.py
```

You will be prompted for:
1. Your Canvas API token (input is hidden)
2. The source (master) course ID
3. The target course ID

## Canvas instance

Configured to connect to `https://courses.lenguax.com`

## Why this script exists

Quizzes copied via Canvas's own "Copy this Course" feature sometimes never
arrive in the target course, with **no error shown anywhere**. Confirmed with
two separate real content_migrations on this account:

- Migration 59 (course 34 → 40, full "copy everything" course copy): completed,
  0 issues logged, but 0 of the source's 16 quizzes appeared in the target.
- Migration 60 (course 34 → 40, a fresh migration using `select[quizzes]` to
  target *only* the 16 quizzes, nothing else): also completed, 0 issues logged,
  still 0 quizzes delivered.

Since a scoped, quizzes-only migration fails identically to a full copy, this
rules out a selection mistake or anything fixable via migration parameters -
it's a genuine bug in Canvas's quiz-copy pipeline on this account/instance. The
right long-term fix is an Instructure support ticket referencing migrations 59
and 60 on course 40 as reproducible evidence. Until/unless that's resolved,
`copy_quizzes_final.py` (reconstructing quizzes question-by-question via the
API) is the working path, with the known limitation that per-answer comments
cannot be copied by any means found so far (see below).

## Known Canvas API quirks (verified empirically, not just from docs)

- **Matching questions**: the GET response's `answers` array uses plain `left` /
  `right` keys for the question's own pairs, but the POST/PUT payload to *create*
  a matching question needs `answer_match_left` / `answer_match_right`. Docs
  describe the write-side names but not the read-side names, so this is easy to
  get wrong (we did, twice) - the script must translate between them.
- **Question-level feedback** (`correct_comments` / `incorrect_comments` /
  `neutral_comments`) *does* work when included in the initial question-creation
  POST, and appears correctly in the Canvas UI.
- **Per-answer comments** (`answer_comments`, the "if student chooses this
  answer" feedback) does **not** persist via the API - confirmed by creating a
  test question, then checking the actual quiz editor in the browser (not just
  reading it back via the API, since Canvas has a related known bug,
  [instructure/canvas-lms#2433](https://github.com/instructure/canvas-lms/issues/2433),
  where some comment fields save but don't round-trip through GET). Both a plain
  POST and a follow-up PUT (JSON and form-encoded, referencing existing answer
  IDs) were tried and failed. This is a real Canvas platform limitation, not a
  request-format bug - don't re-investigate this without new evidence Canvas
  changed something. The script prints a "MANUAL FOLLOW-UP NEEDED" list at the
  end of the run with every skipped comment (quiz, question ID, text) so they
  can be re-typed by hand in the target course - `debug_answer_comments_scan.py`
  can also scan a course for these independently of a copy run.
- `correct_comments` / `incorrect_comments` / `neutral_comments` are copied as
  plain text (HTML tags stripped) rather than verbatim HTML - Canvas displays
  whatever is written to these fields literally rather than rendering markup,
  so copying raw `<p>...</p>` source content produces visible tag soup in the
  UI.
- Quizzes are always created **unpublished** in the target course; publish them
  manually after copying.
- The script has no dedup/upsert logic - re-running it against a target course
  that already has the copied quizzes will create duplicates. If you need to
  re-copy (e.g. after a fix), delete the previously-copied quizzes in the target
  course first.
