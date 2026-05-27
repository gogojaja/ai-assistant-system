import json
from datetime import datetime, date, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "life"
HEALTH_FILE = DATA_DIR / "health.json"

TYPES = {"weight": "体重(kg)", "steps": "步数", "sleep": "睡眠(h)", "heart_rate": "心率(bpm)"}

def _load():
    if not HEALTH_FILE.exists():
        return []
    with open(HEALTH_FILE) as f:
        return json.load(f)

def _save(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(HEALTH_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def record(data_type, value, record_date=None):
    if data_type not in TYPES:
        return f"❌ 不支持的类型：{data_type}。支持：{', '.join(TYPES.keys())}"
    items = _load()
    entry = {
        "type": data_type,
        "value": float(value),
        "date": record_date or date.today().isoformat(),
        "created_at": datetime.now().isoformat()
    }
    items.append(entry)
    _save(items)
    return f"✅ 已记录 {TYPES[data_type]}：{value}（{entry['date']}）"

def report(period="日报"):
    items = _load()
    if not items:
        return "📊 暂无健康数据。"
    today = date.today()
    if period == "日报":
        start = today
    elif period == "周报":
        start = today - timedelta(days=today.weekday())
    elif period == "月报":
        start = today.replace(day=1)
    else:
        return "❌ 支持：日报/周报/月报"

    filtered = [i for i in items if i["date"] >= start.isoformat()]
    if not filtered:
        return f"📊 {period}暂无数据。"
    lines = [f"📊 {period}（{start} ~ {today}）"]
    for t in TYPES:
        vals = [float(i["value"]) for i in filtered if i["type"] == t]
        if vals:
            avg = sum(vals) / len(vals)
            lines.append(f"  {TYPES[t]}: 平均 {avg:.1f}, 最高 {max(vals)}, 最低 {min(vals)}, 记录 {len(vals)} 次")
    return "\n".join(lines)
