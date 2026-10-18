# Rolling Fitness Coach — Dynamic Training & Nutrition Skill

> **Train when you can. Log what you actually did. Let the plan adapt.**

A reusable [Agent Skill](https://agentskills.io/specification) for an AI coach that responds to irregular workouts, crowded gyms, fatigue, exercise substitutions, visual goals, and asynchronous meal reports.

This is **not** a fitness tracking SaaS, automated body-composition measurement, or a medical device. It provides workflow instructions plus an optional offline JSON logging CLI. Persistent storage, image inspection, video search, reminders, and mobile availability require capabilities of the host product.

## 🚀 Try it now — no installation required

### **[▶ Open Rolling Fitness Coach in ChatGPT](https://chatgpt.com/?q=Act%20as%20my%20Rolling%20Fitness%20Coach%20for%20adaptive%20workouts%20and%20nutrition.%20Read%20https%3A%2F%2Fraw.githubusercontent.com%2FAngusliu6%2Fyour-rolling-fitness-coach-%2Fmain%2FSKILL.md%20and%20relevant%20references%2F%20files%20from%20that%20repo%20before%20coaching.%20Adapt%20to%20workouts%20actually%20completed%2C%20time%2C%20recovery%2C%20equipment%20and%20meals.%20Do%20not%20claim%20installation%20or%20persistent%20memory.%20If%20you%20cannot%20access%20GitHub%2C%20ask%20me%20to%20paste%20SKILL.md.%20First%20ask%20whether%20I'd%20like%20to%20plan%20a%20workout%2C%20log%20a%20meal%2C%20or%20set%20up%20a%20profile.)**

Open the link, review the prefilled starter text (if your browser supports it), **press Send**, and tell the coach what you want to do. No CLI, GitHub account, or plugin knowledge needed for this trial.

> **Important:** This is a best-effort, **undocumented** ChatGPT prefill URL, **not** an installation link. It may not prefill on some mobile clients, and it cannot automatically submit a message, install the Skill, or preserve logs across chats. The assistant must be able to read the public source on GitHub.

<details><summary>Fallback: copy/paste this into a new ChatGPT chat</summary>

```text
Act as my Rolling Fitness Coach for adaptive workouts and nutrition. Read https://raw.githubusercontent.com/Angusliu6/your-rolling-fitness-coach-/main/SKILL.md and relevant references/ files from that repo before coaching. Adapt to workouts actually completed, time, recovery, equipment and meals. Do not claim installation or persistent memory. If you cannot access GitHub, ask me to paste SKILL.md. First ask whether I'd like to plan a workout, log a meal, or set up a profile.
```

</details>

For a real installation on an eligible ChatGPT account or workspace, see [Mobile & installation](docs/INSTALL.md). The author's **private** Plugin link is not a public install link.

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

## For developers and eligible Skills users

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
