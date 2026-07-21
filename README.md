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

## Why this script exists - INVESTIGATION IN PROGRESS (paused 2026-07-20)

Quizzes copied via Canvas's own "Copy this Course" feature sometimes never
arrive in the target course, with **no error shown anywhere**. This Canvas
instance is self-hosted on a DigitalOcean droplet (`Canvas-LX`, Rails app at
`/var/canvas`, connect via the DigitalOcean web console at
`cloud.digitalocean.com/droplets/473094510/terminal/ui/?os_user=root` - no
local SSH key set up for it), so - unlike a normal Instructure-hosted
account - a broken/misconfigured install is a real, fixable possibility here,
not just an upstream Canvas bug to file a ticket about.

**Status of the investigation:**

- Migration 59 (course 34 → 40, a genuine full "copy everything" course copy -
  confirmed via server log: `settings` included `everything: true,
  overwrite_quizzes: true`): completed, 0 issues logged, but 0 of the source's
  16 quizzes appeared in the target. **This is still unexplained and is real
  evidence of *something* wrong** - it wasn't run by any of our own scripts.
- Migration 60 (an attempt to test a scoped `select[quizzes]`-only migration
  via `native_copy_quizzes.py`): also showed 0 quizzes delivered, and was
  initially treated as confirming the same bug independent of full-copy
  scope. **That conclusion was wrong.** The server log for migration 60 shows
  its settings only captured a single quiz id (`quizzes: '461'`, the last one
  in the list) instead of all 16 - because the script sent repeated
  `select[quizzes]=<id>` form fields without the trailing `[]`, and Rails'
  param parser treats repeated non-bracketed keys as overwriting a scalar
  (last value wins), not accumulating an array. **Migration 60 is not valid
  evidence of anything** - it tested a broken request, not Canvas's real
  behavior. This has been fixed in `native_copy_quizzes.py` (now sends
  `select[quizzes][]`) but **the fix has not been re-tested yet** - the
  target course (40) was deleted before the retry happened.

**Next step when picking this back up:** re-run `native_copy_quizzes.py`
(source 34, into a fresh target course) with the corrected `[]` syntax and see
whether a properly-formed scoped migration actually succeeds. If it does,
that's a real fix going forward (full fidelity, including per-answer
comments, which `copy_quizzes_final.py` cannot copy) and points to something
specific about full "everything" copies being the broken path. If it still
fails with 0 quizzes delivered even with correct syntax, *that* would be solid
evidence of a genuine install-level problem worth digging into further on the
droplet itself (e.g. checking the `canvas_init.service` unit - currently
failed, though likely just a redundant legacy `script/delayed_job` wrapper
colliding with the already-running `canvas-delayed-job.service`, not
necessarily the cause - or comparing gem versions against the Canvas release
this instance claims to run).

Until this is resolved either way, `copy_quizzes_final.py` (reconstructing
quizzes question-by-question via the classic Quiz Questions API) is the
working fallback, with the known limitation that per-answer comments cannot
be copied by any means found so far (see below).

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
