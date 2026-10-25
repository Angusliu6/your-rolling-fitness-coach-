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


## v1.1 SQLite 结构化训练状态

另提供可选 `scripts/progression_db.py` 与 SQLite 三表 `sessions`、`actual_sets`、`prescriptions`，分别保存训练会话、逐组真实记录、下一次训练建议。字段包括器械身份/负重口径/单位、每组重量、次数、RIR、技术质量、力竭标记、休息秒数和向心/离心动作节奏。建议不可算成真实完成，PR 只在动作及器械可比时计算。详见 `docs/DATA_STORAGE.md` 和 `references/progression-engine.md`。


## v1.2.1 原生聊天训练 UI 数据边界

ChatGPT 对话原生交互区可收集可选的当日体重（原始单位 kg/斤、换算 kg）、`weight_context`（晨重/饭后训练前/训练后/未知）、训练分钟、恢复与逐组 `completed/load/reps/rir`。**提交到同一聊天后**才构成教练能处理的已报告记录。当前 UI 的未提交临时输入不能被宣称已跨回合永久保存。

未勾选=未确认完成，留空重量、次数、RIR=未知而非 0。每组的实际负重必须与目标负重分开，并标注每只哑铃/器械/杠铃/自重等口径。

本仓库的 JSON/SQLite 命令行仍是**独立可选本地持久化工具**，ChatGPT 对话不会自动写入这些文件。不要将私人记录提交至公共 GitHub。
