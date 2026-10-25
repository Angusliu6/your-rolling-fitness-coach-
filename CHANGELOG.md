# Changelog

## v1.2.0 — Interactive tracker, pre-workout bodyweight, core module (2026-10-25)

- Add a real mobile-responsive, dependency-free browser UI: `docs/training-ui.html`, `training-ui.css`, `training-ui.js`.
- Preflight bodyweight/context/time/readiness; editable **per-set** load, reps, RIR, completion, exercise replacements and variable set counts.
- Include core/abs training by default, within the same time budget; provide knee-front fatigue triage guidelines.
- Local browser save, JSON import/export and completed-sets-only export compatible with existing JSON logging CLI.
- State explicitly that standalone UI and Skill do not automatically sync to ChatGPT, hosted database, or SQLite.



## 1.0.0 — 2026-10-18

- Rolling workout coach rules: variable availability, recent work sets, fatigue and equipment alternatives.
- Nutrition reporting with consumed/ordered/planned distinction.
- Technique cues and verifiable exercise demonstration sourcing rules.
- Offline JSON fitness diary CLI, sample inputs, unit tests and behavioral eval prompts.
- Public-facing bilingual README and mobile installation notes.


## v1.1.0 — Per-set progressive overload & private SQLite (2026-10-24)

- Add optional SQLite per-set actual records separated from proposed workouts.
- Add strict comparable-equipment/load-basis PR and conservative per-set weight/rep recommendations.
- Track tempo, set rest, RIR, effort and failure, avoiding unsafe automatic weight jumps.
- Add a synthetic example, architecture and privacy guide, and 15 progression-engine unit tests.
- Clarify that ChatGPT chat/plugin usage does not itself guarantee mobile persistence.
