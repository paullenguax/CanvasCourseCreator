# Canvas Course Creator

A Python script that copies all quizzes (including questions) from one Canvas LMS course to another.

## What it does

Given a source course ID and a target course ID, it fetches every quiz from the source course via the Canvas API and recreates them in the target course — including all questions, answer options, and settings (time limit, shuffle answers, scoring policy, etc.).

Supports question types including multiple choice, true/false, and matching questions.

## Files

- `copy_quizzes_final.py` — the main script to use
- `copy_quizzes.py` — earlier version

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
  changed something.
- Quizzes are always created **unpublished** in the target course; publish them
  manually after copying.
- The script has no dedup/upsert logic - re-running it against a target course
  that already has the copied quizzes will create duplicates. If you need to
  re-copy (e.g. after a fix), delete the previously-copied quizzes in the target
  course first.
