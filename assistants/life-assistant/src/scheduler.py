import json
import uuid
from datetime import datetime, date
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "life"
SCHEDULE_FILE = DATA_DIR / "schedules.json"

def _load():
    if not SCHEDULE_FILE.exists():
        return []
    with open(SCHEDULE_FILE) as f:
        return json.load(f)

def _save(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add(title, time_str, location="", notes=""):
    items = _load()
    item = {
        "id": uuid.uuid4().hex[:8],
        "title": title,
        "time": time_str,
        "location": location,
        "notes": notes,
        "created_at": datetime.now().isoformat()
    }
    items.append(item)
    _save(items)
    return item

def list_items(date_str=None):
    items = _load()
    if not items:
        return "📅 暂无日程安排。"
    if date_str:
        items = [i for i in items if i["time"].startswith(date_str)]
        if not items:
            return f"📅 {date_str} 没有日程。"
    lines = ["📋 日程列表："]
    for i, item in enumerate(sorted(items, key=lambda x: x["time"]), 1):
        loc = f" 📍{item['location']}" if item.get("location") else ""
        note = f" 💬{item['notes']}" if item.get("notes") else ""
        lines.append(f"  {i}. [{item['id']}] {item['time']} {item['title']}{loc}{note}")
    return "\n".join(lines)

def delete(item_id):
    items = _load()
    new_items = [i for i in items if i["id"] != item_id]
    if len(new_items) == len(items):
        return f"❌ 未找到 ID 为 {item_id} 的日程。"
    _save(new_items)
    return f"✅ 已删除日程 {item_id}。"

def search(keyword):
    items = _load()
    results = [i for i in items if keyword.lower() in i["title"].lower()]
    if not results:
        return f"🔍 未找到包含「{keyword}」的日程。"
    lines = [f"🔍 搜索「{keyword}」结果："]
    for item in results:
        lines.append(f"  [{item['id']}] {item['time']} {item['title']}")
    return "\n".join(lines)

def get_upcoming(minutes=30):
    items = _load()
    now = datetime.now()
    reminders = []
    for item in items:
        try:
            t = datetime.fromisoformat(item["time"])
            delta = (t - now).total_seconds()
            if 0 <= delta <= minutes * 60:
                reminders.append(item)
        except ValueError:
            continue
    return reminders
