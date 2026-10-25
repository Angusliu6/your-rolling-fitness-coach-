# Database & PR Tracker / 动态训练数据库使用指南

## 选择：Skill + SQLite，而不是在 GitHub 保存每个人的数据

| 实施层级 | 存储 | 何时选 |
| --- | --- | --- |
| **当前开源 MVP（推荐）** | `SKILL.md` 负责智能教练对话，`scripts/progression_db.py` 使用本机 **SQLite** 保存每次实际组数据 | 个人使用 / 单设备 / 隐私优先 / 零额外服务 |
| **下一步手机同步** | 客户端 + 受认证的 API + 托管 **PostgreSQL** (或其他可靠托管 DB) | 多用户、多设备、共享对话状态 / 真正“打开手机就用” |
| **只写在 Skill 里** | 只存规则；默认不能永久保存数据 | 纯对话试用；跨会话不保证 |
| **把真实 SQLite DB push 到 Public GitHub** | ❌ 不要这样做 | 可能暴露体重、训练日期、照片或健康记录；Git 版本历史会保留旧版本 |

SQLite 省掉数据库服务器，特别适合 MVP；但 ChatGPT 私人插件不自动获得用户设备文件系统写入权，因此**安装 Skill 不等于自动启用 SQLite 持久存储**。

## 第一次运行（开发者或本地 Python 环境）

```sh
python scripts/progression_db.py --db private/fitness.sqlite3 init
python scripts/progression_db.py --db private/fitness.sqlite3 log --input assets/progression.example.json
python scripts/progression_db.py --db private/fitness.sqlite3 plan --exercise example_machine_chest_press --equipment machine-A-model-example --load-basis machine_stack --unit kg --sets 3 --rep-min 8 --rep-max 12 --increment 2.5 --rest-seconds 120 --eccentric-seconds 2 --concentric-seconds 1
python scripts/progression_db.py --db private/fitness.sqlite3 pr --exercise example_machine_chest_press --equipment machine-A-model-example --load-basis machine_stack --unit kg
python -m unittest discover -s tests -v
```

命令行输入必须来自用户**实际确认**的逐组数据；`assets/progression.example.json` 为**虚构示例**。练前生成计划默认**不会写回数据库**；添加 `--save` 才会保存成 `prescriptions`（计划），但永远不算实际完成。

## 主要表格

| 表 | 核心字段 | 作用 |
| --- | --- | --- |
| `sessions` | 日期、状态、疲劳、疼痛 | 一次训练的总体环境 |
| `actual_sets` | exercise、equipment、load_basis、unit、load、reps、rir、form、failure、rest_seconds、eccentric_seconds、concentric_seconds | 真正完成的每个组；自动计算进展的数据基础 |
| `prescriptions` | 目标组数/重量/次数/休息/节奏、理由 | 生成的建议，不算已完成 |

公开示例只包含虚构数据，不包含开发者真实日志、照片或私人资料。

## 技术假设和进阶

- 当前脚本按**动作+器械+重量口径+单位**严格匹配，机器不同不能直接比较配重；你可以统一动作名称，但不应把不明确名称强行规范化。
- 需要 `reps`、`rir`、`form` 和休息等信息才能给出有依据的下一次逐组目标；缺数据会返回 `verify`/`baseline` 而不是凭空创造历史成绩。
- 需要训练中交互式写入、跨设备备份、OAuth 账户和家人数据隔离时，再开发服务端 API，托管 PostgreSQL 等并确保单用户数据隔离、备份、可导出和可删除。
- 不能把私有数据库作为插件 ZIP 的预置文件共享；每个用户都应拥有自己的数据空间。


## v1.2 独立浏览器逐组 UI

手机或桌面浏览器可以打开 `docs/training-ui.html`（需同时保留同目录的 `training-ui.js`、`training-ui.css`）。在「训练前」填写体重和称重条件，然后进入逐组记录；每组重量、次数、RIR 和完成标记独立。浏览器本地 `localStorage` 会保存当前状态。使用「导出本地 JSON 备份」可迁移到另一设备后手工导入。

「导出 CLI 兼容训练 JSON」仅导出确认完成的组，执行：

```bash
python scripts/coach_log.py add-workout --file athlete.json --input rolling-fitness-workout-YYYY-MM-DD.json
# 当日有记录体重时，另外执行（只提供自己实际测得的数据）：
python scripts/coach_log.py add-weight --file athlete.json --date YYYY-MM-DD --kg YOUR_MEASURED_KG --context after_meal_before_workout
```

**不能直接把浏览器 UI 导出文件当作 SQLite `progression_db.py` 的输入**；两个数据协议不同。网页目前没有后端连接、云同步或对 ChatGPT 的自动写回。请勿把导出的私人备份提交到公开仓库。
