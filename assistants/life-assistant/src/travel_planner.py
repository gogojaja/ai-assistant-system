import json
import uuid
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "life"
TRAVEL_FILE = DATA_DIR / "travels.json"


def _load():
    if not TRAVEL_FILE.exists():
        return []
    with open(TRAVEL_FILE) as f:
        return json.load(f)


def _save(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(TRAVEL_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def create(destination, start_date, end_date="", notes=""):
    trips = _load()
    trip = {
        "id": uuid.uuid4().hex[:8],
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "notes": notes,
        "activities": [],
        "packing_list": [],
        "created_at": datetime.now().isoformat(),
    }
    trips.append(trip)
    _save(trips)
    return trip


def list_trips():
    trips = _load()
    if not trips:
        return "🗺️ 暂无旅行计划。"
    lines = ["🗺️ 旅行计划："]
    now = datetime.now().isoformat()[:10]
    for i, t in enumerate(trips, 1):
        dates = f"{t['start_date']} ~ {t['end_date']}" if t.get("end_date") else t["start_date"]
        badge = " 📍进行中" if t["start_date"] <= now <= (t.get("end_date") or t["start_date"]) else ""
        lines.append(f"  {i}. [{t['id']}] {t['destination']} ({dates}){badge}")
    return "\n".join(lines)


def view(trip_id):
    trips = _load()
    for t in trips:
        if t["id"] == trip_id:
            lines = [f"🗺️ {t['destination']}"]
            dates = f"{t['start_date']} ~ {t['end_date']}" if t.get("end_date") else t["start_date"]
            lines.append(f"  日期：{dates}")
            if t.get("notes"):
                lines.append(f"  备注：{t['notes']}")

            acts = t.get("activities", [])
            if acts:
                lines.append(f"\n📌 行程活动（{len(acts)}项）：")
                for j, a in enumerate(acts, 1):
                    d = f" [{a.get('date', '')}]" if a.get("date") else ""
                    lines.append(f"  {j}.{d} {a['item']}")
            else:
                lines.append("\n📌 暂无行程安排。")

            pack = t.get("packing_list", [])
            if pack:
                lines.append(f"\n🧳 行李清单（{sum(1 for p in pack if p.get('checked'))}/{len(pack)}）：")
                for j, p in enumerate(pack, 1):
                    ck = "✅" if p.get("checked") else "⬜"
                    lines.append(f"  {j}. {ck} {p['item']}")
            else:
                lines.append("\n🧳 行李清单为空。")
            return "\n".join(lines)
    return f"❌ 未找到旅行 ID：{trip_id}"


def add_activity(trip_id, item, date_str=""):
    trips = _load()
    for t in trips:
        if t["id"] == trip_id:
            activity = {"item": item, "date": date_str}
            t.setdefault("activities", []).append(activity)
            _save(trips)
            return f"✅ 已添加活动：{item}"
    return f"❌ 未找到旅行 ID：{trip_id}"


def pack_item(trip_id, item):
    trips = _load()
    for t in trips:
        if t["id"] == trip_id:
            t.setdefault("packing_list", []).append({"item": item, "checked": False})
            _save(trips)
            return f"✅ 已添加行李：{item}"
    return f"❌ 未找到旅行 ID：{trip_id}"


def toggle_pack(trip_id, item_keyword):
    trips = _load()
    for t in trips:
        if t["id"] == trip_id:
            pack = t.setdefault("packing_list", [])
            for p in pack:
                if item_keyword.lower() in p["item"].lower():
                    p["checked"] = not p.get("checked")
                    status = "✅ 已打包" if p["checked"] else "⬜ 取消打包"
                    _save(trips)
                    return f"{status}：{p['item']}"
            return f"❌ 未找到行李：{item_keyword}"
    return f"❌ 未找到旅行 ID：{trip_id}"


def delete(trip_id):
    trips = _load()
    new_trips = [t for t in trips if t["id"] != trip_id]
    if len(new_trips) == len(trips):
        return f"❌ 未找到旅行 ID：{trip_id}"
    deleted = [t for t in trips if t["id"] == trip_id][0]
    _save(new_trips)
    return f"✅ 已删除旅行：{deleted['destination']} ({deleted['start_date']})"


def delete_activity(trip_id, idx):
    trips = _load()
    for t in trips:
        if t["id"] == trip_id:
            acts = t.get("activities", [])
            if 1 <= idx <= len(acts):
                removed = acts.pop(idx - 1)
                _save(trips)
                return f"✅ 已删除活动：{removed['item']}"
            return f"❌ 序号超出范围（1-{len(acts)}）"
    return f"❌ 未找到旅行 ID：{trip_id}"
