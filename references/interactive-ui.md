# Interactive workout tracker protocol (v1.2)

This is an **AI host behavior specification**, plus a working standalone example in [docs/training-ui.html](../docs/training-ui.html). A prompt-only Skill **cannot force** an AI client to render interactive controls, preserve UI state across chat messages, or sync to cloud storage. If interactive controls are unsupported, return a compact copyable table / ask for natural-language per-set results instead. Do not claim any ChatGPT UI automatically executes repository JavaScript.

## Required flow: preflight → active → review

### Preflight (before exercise list)

Ask for **today's body weight (optional, editable)** with units kg / 斤 (convert 1斤=0.5kg); collect weight context: `morning_fasted`, `before_workout`, `after_meal_before_workout`, `after_workout`, `unknown`. Also date, available minutes, readiness/recovery, pain and priority muscles. Pre-populate only **confirmed current-session** values; never substitute an old weigh-in as today's measurement. Non-fasted/after-meal entries should not be compared directly to fasted morning trend or interpreted as rapid lean mass gain.

### Active workout (one row per real set)

For **every** exercise and set, render if the host supports it:

| Field | Rule |
| --- | --- |
| `completed` | User-controlled; initially **false**; only true counts as actual |
| `load` | Editable numeric >=0, blank means **unknown**, not 0 |
| `unit` | Default kg, optionally lb |
| `load_basis` | Specify `per_dumbbell`, `machine_stack`, `barbell_total`, `bodyweight`, or `other`; do not compare across bases |
| `reps` | Editable integer >=0, blank means unknown |
| `rir` | Editable 0–10 estimate, blank means unknown |
| `set_kind` | Work vs warmup; warmup not counted as working volume |
| `exercise` | Editable/replaceable; show alternative for occupied machines |
| `notes` | Optional fatigue, pain, form; shoulder fatigue is not proof of muscle growth |

Allow adding/removing sets and swapping movements without losing other exercises' data. A proposed load/rep target is **not** an actual record until the user reports and confirms it. Never pre-mark planned sets as completed. If user says "did all groups, can't remember reps", mark completed with reps missing—not invented. Do not automatically push personal workout info to a public repository.

### Core/abs module is a first-class planning requirement

For aesthetic V-taper + visible abs goals, schedule **2–3 direct core sets** most sessions, generally across two sessions/week. Rotate:
- Cable crunch: 2–3 × 10–15, controlled trunk flexion and stable pelvis; if cable occupied, use reverse crunch on mat.
- Reverse crunch: 2–3 × 10–15, controlled posterior pelvic tilt, do not swing legs.
- Optional dead bug: 2–3 × 6–10 per side when lower back control/comfort more important than loaded flexion.

Include these in the **same** time budget; reduce other lower-priority sets to fit. Do not suggest spot reduction (ab training strengthens muscles but cannot selectively remove belly fat). If user has severe pain, refer for medical evaluation before prescribing loaded training.

### Summary and persistence

Display progress as completed / planned sets; copyable message includes bodyweight+condition and real per-set weights/reps/RIR. Export only confirmed sets to `scripts/coach_log.py` compatible JSON; preserve blank fields as `null`. A browser-local backup JSON may include planned and incomplete rows explicitly, separate from confirmed work.

`docs/training-ui.html` is mobile responsive, offline-first and saves **only in that browser's localStorage**, with manual import/export. It has no server, network calls, OAuth, SQLite integration, or ChatGPT synchronization. The optional Python SQLite engine is a **separate local program**; saving in the webpage does not mutate that database.

**Privacy:** This repository contains code and synthetic examples only. User-specific bodyweight, chat transcripts, photos, injuries and detailed workout histories must not be committed.

## Host-generated UI fallback

- When host supports stateful interactive controls: preflight weight/context/time; editable set rows with `completed, load, reps, RIR`; submission action returning a plain-text confirmed log for the coach to process.
- When host has no interactive controls: compact Markdown table plus natural-language report instructions; keep conversation-driven logging working.
- Clear that simply clicking a browser UI's checkbox does not automatically update ChatGPT memory; must submit or copy/share the log.
