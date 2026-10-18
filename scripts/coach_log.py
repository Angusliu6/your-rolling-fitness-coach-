#!/usr/bin/env python3
"""Optional local, offline rolling workout/food log. Never sends user data online."""
import argparse
import copy
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

EMPTY = {"schema_version": 1, "profile": {}, "workouts": [], "food": [], "weights": []}


def load(path):
    with open(path, encoding="utf-8") as f:
        state = json.load(f)
    if not isinstance(state, dict) or state.get("schema_version") != 1:
        raise ValueError("Unsupported or missing schema_version (expected 1)")
    for key in ("workouts", "food", "weights"):
        if not isinstance(state.get(key), list):
            raise ValueError(f"Missing or invalid list: {key}")
    return state


def save(path, state):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    with open(temp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(temp, path)


def valid_date(value):
    return date.fromisoformat(value)


def read_payload(filename):
    with open(filename, encoding="utf-8") as f:
        doc = json.load(f)
    if not isinstance(doc, dict):
        raise ValueError("Input must be a JSON object")
    return doc


def number(value, field, allow_none=False):
    if value is None and allow_none:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError(f"{field} must be a nonnegative number")
    return value


def validate_workout(doc):
    valid_date(doc["date"])
    if not isinstance(doc.get("exercises"), list) or not doc["exercises"]:
        raise ValueError("Workout must contain completed exercises")
    if doc.get("duration_min") is not None:
        number(doc["duration_min"], "duration_min")
    for e in doc["exercises"]:
        if not isinstance(e.get("name"), str) or not e["name"].strip():
            raise ValueError("Each exercise needs a name")
        if not isinstance(e.get("muscles", []), list):
            raise ValueError("muscles must be a list")
        sets = e.get("sets")
        if not isinstance(sets, list) or not sets:
            raise ValueError("Each exercise needs at least one actually completed set")
        for s in sets:
            if not isinstance(s, dict):
                raise ValueError("Each set must be an object")
            if s.get("kg") is not None:
                number(s["kg"], "kg")
            if s.get("reps") is not None:
                number(s["reps"], "reps")
            if s.get("rir") is not None:
                if number(s["rir"], "rir") > 10:
                    raise ValueError("RIR > 10 is not a meaningful working-set estimate")
            if s.get("type", "work") not in ("work", "warmup"):
                raise ValueError("set type must be work or warmup")
    return doc


def validate_food(doc):
    valid_date(doc["date"])
    if not doc.get("name") or not isinstance(doc["name"], str):
        raise ValueError("Food event requires a name")
    if doc.get("status") not in ("consumed", "ordered", "planned", "unknown"):
        raise ValueError("status must be consumed/ordered/planned/unknown")
    for field in ("estimated_protein_g", "estimated_kcal"):
        if field in doc and doc[field] is not None:
            number(doc[field], field)
    return doc


def add_workout(state, doc):
    state["workouts"].append(validate_workout(doc))


def add_food(state, doc):
    state["food"].append(validate_food(doc))


def add_weight(state, day, kg, context):
    valid_date(day)
    if kg <= 0:
        raise ValueError("kg must be greater than zero")
    state["weights"].append({"date": day, "kg": kg, "context": context})


def summary(state, days=14, today=None):
    today = today or date.today()
    start = today - timedelta(days=days - 1)
    counts = {}
    workouts = []
    for w in state["workouts"]:
        if not start <= valid_date(w["date"]) <= today:
            continue
        workouts.append(w)
        for e in w["exercises"]:
            count = sum(1 for s in e["sets"] if s.get("type", "work") == "work")
            for muscle in set(e.get("muscles", [])):
                counts[muscle] = counts.get(muscle, 0) + count
    consumed = []
    incomplete = []
    for f in state["food"]:
        if not start <= valid_date(f["date"]) <= today:
            continue
        (consumed if f["status"] == "consumed" else incomplete).append(f)
    # Sum only explicit estimates; report coverage so missing data are not mistaken for zero.
    protein_known = [f["estimated_protein_g"] for f in consumed if f.get("estimated_protein_g") is not None]
    kcal_known = [f["estimated_kcal"] for f in consumed if f.get("estimated_kcal") is not None]
    weights = [w for w in state["weights"] if start <= valid_date(w["date"]) <= today]
    morning = [w["kg"] for w in weights if w.get("context") == "morning"]
    return {
        "window": {"start": start.isoformat(), "end": today.isoformat(), "days": days},
        "completed_workouts": len(workouts),
        "direct_working_sets_by_muscle": dict(sorted(counts.items())),
        "food_consumed_events_reported": len(consumed),
        "food_events_not_confirmed_consumed": len(incomplete),
        "protein_known_g_sum_not_daily_total": round(sum(protein_known), 1),
        "protein_known_event_count": len(protein_known),
        "calories_known_kcal_sum_not_daily_total": round(sum(kcal_known), 1),
        "calories_known_event_count": len(kcal_known),
        "morning_weight_average_kg": round(sum(morning) / len(morning), 2) if morning else None,
        "morning_weight_measurements": len(morning),
        "note": "These are reported events only. Missing meals, workouts, sets and macros are unknown, not zero; muscle groups are directly tagged, not independently inferred."
    }


def main(argv=None):
    p = argparse.ArgumentParser(description="Local, privacy-preserving fitness & nutrition record CLI")
    sub = p.add_subparsers(dest="command", required=True)
    for command in ("init", "add-workout", "add-food", "add-weight", "summary"):
        s = sub.add_parser(command)
        s.add_argument("--file", required=True, type=Path)
        if command in ("add-workout", "add-food"):
            s.add_argument("--input", required=True, type=Path)
        elif command == "add-weight":
            s.add_argument("--date", required=True)
            s.add_argument("--kg", required=True, type=float)
            s.add_argument("--context", default="unknown")
        elif command == "summary":
            s.add_argument("--days", type=int, default=14)
            s.add_argument("--today", help="ISO date override for testing")
    a = p.parse_args(argv)
    try:
        if a.command == "init":
            if a.file.exists():
                raise ValueError("Refusing to overwrite existing file")
            save(a.file, copy.deepcopy(EMPTY))
            print(f"Initialized local log: {a.file}")
            return 0
        state = load(a.file)
        if a.command == "add-workout":
            add_workout(state, read_payload(a.input))
            save(a.file, state)
            print("Added confirmed workout")
        elif a.command == "add-food":
            add_food(state, read_payload(a.input))
            save(a.file, state)
            print("Added food event")
        elif a.command == "add-weight":
            add_weight(state, a.date, a.kg, a.context)
            save(a.file, state)
            print("Added weight")
        elif a.command == "summary":
            if a.days < 1 or a.days > 365:
                raise ValueError("days must be 1..365")
            print(json.dumps(summary(state, a.days, date.fromisoformat(a.today) if a.today else None), indent=2, ensure_ascii=False))
        return 0
    except (ValueError, KeyError, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
