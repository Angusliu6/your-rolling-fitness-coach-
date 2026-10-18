# Rolling Fitness Coach — Dynamic Training & Nutrition Skill

> **Train when you can. Log what you actually did. Let the plan adapt.**

A reusable [Agent Skill](https://agentskills.io/specification) for an AI coach that responds to irregular workouts, crowded gyms, fatigue, exercise substitutions, visual goals, and asynchronous meal reports.

This is **not** a fitness tracking SaaS, automated body-composition measurement, or a medical device. It provides workflow instructions plus an optional offline JSON logging CLI. Persistent storage, image inspection, video search, reminders, and mobile availability require capabilities of the host product.

## What it solves

- **Irregular training:** You might be free for 25, 45, or 60 minutes at unpredictable times. The coach plans from actual context instead of assuming fixed gym days.
- **Partial workouts:** Only completed work sets enter the log; warm-ups and planned-but-skipped sets never count as completed work.
- **Equipment conflicts:** If a machine is occupied, find a movement-pattern-compatible replacement and recalibrate loads.
- **Weak mind–muscle connection:** Address setup, range of motion, effort, and fatigue without treating subjective muscle sensation as proof of effectiveness or safety.
- **Form guidance:** Explain sets, reps, rest, RIR, cues, mistakes, and—when browsing is supported—link to verifiable demonstrations.
- **Nutrition without rigid meal logs:** Distinguish consumed, ordered, planned, and unknown. Estimate only what reports support, and connect food intake to training and recovery.
- **Progressive overload:** Track per-set load/reps/RIR, recovery, training exposure, and longitudinal bodyweight trends to make small evidence-aware changes.

## User experience

```text
You: I'm at the gym for 40 minutes. My last session was chest and my shoulders are still sore.
Coach: Here's a leg/back-biased workout with exact sets, reps, rest and substitutions.
You: Leg press: 70 kg x 12, 11, 10. The next machine is occupied and I have 12 minutes left.
Coach: Logged 3 confirmed sets. Replace the machine, reduce remaining volume, and prioritize safe work.
You: Lunch was rice, chicken, and vegetables. I haven't had my ordered protein shake yet.
Coach: Log the meal as an estimate, do not count the shake, and recommend a next meal.
```

## Start

1. Open [`SKILL.md`](SKILL.md). It explains when to read each topic file under [`references/`](references/).
2. For supported ChatGPT accounts, see [installation and mobile instructions](docs/INSTALL.md).
3. For compatible Agent Skills hosts, install this entire folder into the host's skill directory.
4. For an optional local CLI, use Python 3.9+:

```bash
python scripts/coach_log.py init --file athlete.json
python scripts/coach_log.py add-workout --file athlete.json --input assets/workout.example.json
python scripts/coach_log.py summary --file athlete.json --days 14
python -m unittest discover -s tests -v
```

The example JSON files contain fictional entries, not real user logs.

## Architecture

- `SKILL.md` — workflow router and safety rules.
- `references/training-engine.md` — rolling training scheduling and progressive overload.
- `references/nutrition-engine.md` — asynchronous meals, macros and caffeine.
- `references/exercise-demos.md` — form and verifiable sources.
- `references/intake-visual-assessment.md` — cautious photo/measurement interpretation.
- `references/data-model.md` + `scripts/coach_log.py` — offline optional persistence.
- `tests/` — local CLI unit tests.
- `evals/` — behavioral evaluation prompts (not yet an end-to-end AI test result).

## Principles & limitations

Training plans are hypotheses; completed sessions are evidence. Exercise volume is based on real sets, not aspirational plans. The model should minimize unnecessary questions, clearly label uncertainty, never invent exercise links or measured body fat, and handle pain differently from routine fatigue.

**Privacy:** This open-source package contains no real personal fitness logs, photographs, private chats, or personally identifying data. User-specific tracking must remain under the user's control; an offline CLI never transmits records. See [safety and privacy policy](references/safety-privacy.md).

## Contributing

Suggestions and fixes are welcome. Please use anonymized, synthetic examples and review [CONTRIBUTING.md](CONTRIBUTING.md) before submitting. Licensed under [MIT](LICENSE).
