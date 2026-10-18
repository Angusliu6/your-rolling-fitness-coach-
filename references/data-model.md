# 本地状态协议

`assets/state.template.json` 是一个没有真实个人信息的模板；`scripts/coach_log.py` 可单文件保存训练、饮食、体重。**默认不做自动同步。**

## 字段语义

- `profile`: 昵称（可为空）、目标、训练经验、目标肌群、每周预计训练次数、限制等。
- `workouts`: 仅用户确认的训练报告。字段 `date`、`duration_min`、`exercises`、`fatigue_0_10`、`pain_notes`；exercise 由 `name`、`muscles`、`sets` 组成；每组 `kg` / `reps` / `rir` 允许 null。
- `food`: 每个摄入事件的 `date`、`time`、`name`、`status`、`quantity`、`estimated_protein_g`、`estimated_kcal`；状态 `consumed` 才纳入汇总。
- `weights`: `date`、`kg`、`context`（如 morning / post_workout）；应按可比情境评估趋势。
- `plans`: 可保存 `planned` 训练，但不能计入已完成量（基础CLI当前不会自动保存计划）。

## 不要构造的字段

未报告的重量/次数/食物份量，不得从典型示例自动填充。某动作重量必须注明机器配重块总数、杠铃总重量或每只哑铃（可放在 `notes` 中），否则不同器材难比较。

## 示例命令

```
python scripts/coach_log.py init --file athlete.json
python scripts/coach_log.py add-workout --file athlete.json --input workout.json
python scripts/coach_log.py add-food --file athlete.json --input meal.json
python scripts/coach_log.py add-weight --file athlete.json --date 2026-02-01 --kg 64.2 --context morning
python scripts/coach_log.py summary --file athlete.json --days 14
```

输入 JSON 模板见 `assets/`。脚本仅把数据写入本地 JSON，具体训练建议需由教练模型解读。用户可直接删除该 JSON 文件清除本地存储。
