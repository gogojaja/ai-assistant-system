import json
import uuid
from datetime import datetime, date
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "life"
WORKOUT_FILE = DATA_DIR / "workouts.json"


def _load():
    if not WORKOUT_FILE.exists():
        return []
    with open(WORKOUT_FILE) as f:
        return json.load(f)


def _save(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(WORKOUT_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def create(name):
    plans = _load()
    plan = {
        "id": uuid.uuid4().hex[:8],
        "name": name,
        "exercises": [],
        "logs": [],
        "created_at": datetime.now().isoformat(),
    }
    plans.append(plan)
    _save(plans)
    return plan


def list_plans():
    plans = _load()
    if not plans:
        return "🏋️ 暂无锻炼计划。"
    lines = ["🏋️ 锻炼计划："]
    for i, p in enumerate(plans, 1):
        total_logs = len(p.get("logs", []))
        lines.append(f"  {i}. [{p['id']}] {p['name']} — 训练 {total_logs} 次")
    return "\n".join(lines)


def view(plan_id):
    plans = _load()
    for p in plans:
        if p["id"] == plan_id:
            lines = [f"🏋️ {p['name']}"]
            exs = p.get("exercises", [])
            if exs:
                lines.append(f"\n📋 训练项目（{len(exs)}项）：")
                for j, e in enumerate(exs, 1):
                    lines.append(f"  {j}. {e['name']}  {e['sets']}x{e['reps']}")
            else:
                lines.append("\n📋 暂无训练项目。")
            logs = p.get("logs", [])
            if logs:
                lines.append(f"\n📅 训练记录（共{len(logs)}次）：")
                recent = sorted(logs, key=lambda x: x["date"], reverse=True)[:5]
                for lr in recent:
                    note = f" — {lr['note']}" if lr.get("note") else ""
                    lines.append(f"  {lr['date']}{note}")
            return "\n".join(lines)
    return f"❌ 未找到计划 ID：{plan_id}"


def add_exercise(plan_id, name, sets=3, reps=12):
    plans = _load()
    for p in plans:
        if p["id"] == plan_id:
            p.setdefault("exercises", []).append({
                "name": name,
                "sets": int(sets),
                "reps": int(reps),
            })
            _save(plans)
            return f"✅ 已添加训练：{name} {sets}x{reps}"
    return f"❌ 未找到计划 ID：{plan_id}"


def log_workout(plan_id, note=""):
    plans = _load()
    for p in plans:
        if p["id"] == plan_id:
            p.setdefault("logs", []).append({
                "date": date.today().isoformat(),
                "note": note,
            })
            _save(plans)
            return f"✅ 已记录 {p['name']} {date.today().isoformat()} 训练完成"
    return f"❌ 未找到计划 ID：{plan_id}"


def history(plan_id):
    plans = _load()
    for p in plans:
        if p["id"] == plan_id:
            logs = p.get("logs", [])
            if not logs:
                return f"📅 {p['name']} 暂无训练记录。"
            lines = [f"📅 {p['name']} 训练历史（共{len(logs)}次）："]
            for lr in sorted(logs, key=lambda x: x["date"], reverse=True):
                note = f" — {lr['note']}" if lr.get("note") else ""
                lines.append(f"  {lr['date']}{note}")
            return "\n".join(lines)
    return f"❌ 未找到计划 ID：{plan_id}"


def delete(plan_id):
    plans = _load()
    new_plans = [p for p in plans if p["id"] != plan_id]
    if len(new_plans) == len(plans):
        return f"❌ 未找到计划 ID：{plan_id}"
    deleted = [p for p in plans if p["id"] == plan_id][0]
    _save(new_plans)
    return f"✅ 已删除计划：{deleted['name']}"
