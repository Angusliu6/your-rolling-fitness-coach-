import importlib.util
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "coach_log.py"
spec = importlib.util.spec_from_file_location("coach_log", SCRIPT)
coach_log = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coach_log)


class WorkoutNutritionLogTests(unittest.TestCase):
    def setUp(self):
        self.state = json.loads(json.dumps(coach_log.EMPTY))

    def test_actual_working_sets_only(self):
        coach_log.add_workout(self.state, {
            "date": "2026-02-01",
            "exercises": [
                {"name": "lat pulldown", "muscles": ["lats"], "sets": [
                    {"type": "warmup", "kg": 20, "reps": 15},
                    {"type": "work", "kg": 40, "reps": 12},
                    {"type": "work", "kg": 40, "reps": 10}]}
            ]})
        s = coach_log.summary(self.state, 7, date(2026, 2, 3))
        self.assertEqual(s["completed_workouts"], 1)
        self.assertEqual(s["direct_working_sets_by_muscle"]["lats"], 2)

    def test_unconsumed_events_not_counted(self):
        coach_log.add_food(self.state, {"date": "2026-02-01", "name": "coffee", "status": "ordered", "estimated_kcal": 50})
        coach_log.add_food(self.state, {"date": "2026-02-01", "name": "oatmeal", "status": "consumed", "estimated_kcal": 200})
        s = coach_log.summary(self.state, 7, date(2026, 2, 3))
        self.assertEqual(s["calories_known_kcal_sum_not_daily_total"], 200)
        self.assertEqual(s["food_events_not_confirmed_consumed"], 1)

    def test_missing_macros_are_unknown_not_zero(self):
        coach_log.add_food(self.state, {"date": "2026-02-01", "name": "banana", "status": "consumed"})
        s = coach_log.summary(self.state, 7, date(2026, 2, 3))
        self.assertEqual(s["protein_known_event_count"], 0)
        self.assertEqual(s["food_consumed_events_reported"], 1)

    def test_weight_context_morning_only(self):
        coach_log.add_weight(self.state, "2026-02-01", 65.0, "morning")
        coach_log.add_weight(self.state, "2026-02-02", 63.0, "post_workout")
        s = coach_log.summary(self.state, 7, date(2026, 2, 3))
        self.assertEqual(s["morning_weight_average_kg"], 65.0)
        self.assertEqual(s["morning_weight_measurements"], 1)

    def test_invalid_food_state(self):
        with self.assertRaises(ValueError):
            coach_log.add_food(self.state, {"date": "2026-02-01", "name": "coffee", "status": "sentiment"})

    def test_no_planned_workouts_as_completed(self):
        s = coach_log.summary(self.state, 7, date(2026, 2, 3))
        self.assertEqual(s["completed_workouts"], 0)

    def test_save_load(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "athlete.json"
            coach_log.save(path, self.state)
            self.assertEqual(coach_log.load(path), self.state)

    def test_historic_records_excluded(self):
        coach_log.add_workout(self.state, {"date":"2025-01-01", "exercises":[{"name":"squat", "muscles":["quads"],"sets":[{"kg":40,"reps":8}]}]})
        s = coach_log.summary(self.state, 7, date(2026,2,3))
        self.assertEqual(s["completed_workouts"],0)


if __name__ == "__main__":
    unittest.main()
