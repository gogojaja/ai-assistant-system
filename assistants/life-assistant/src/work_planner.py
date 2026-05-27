import json
import uuid
from datetime import datetime, date
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "life"
WORK_FILE = DATA_DIR / "works.json"

STATUS_ICON = {"todo": "📋", "doing": "🔄", "done": "✅"}
STATUS_LABEL = {"todo": "待办", "doing": "进行中", "done": "已完成", "all": "全部"}
STATUS_MAP = {v: k for k, v in STATUS_LABEL.items()}
STATUS_MAP.update({"todo": "todo", "doing": "doing", "done": "done", "all": "all"})
PRIORITIES = ["高", "中", "低"]


def _load():
    if not WORK_FILE.exists():
        return []
    with open(WORK_FILE) as f:
        return json.load(f)


def _save(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(WORK_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def create(title, priority="中", deadline=""):
    items = _load()
    item = {
        "id": uuid.uuid4().hex[:8],
        "title": title,
        "status": "todo",
        "priority": priority if priority in PRIORITIES else "中",
        "deadline": deadline,
        "notes": "",
        "created_at": datetime.now().isoformat(),
    }
    items.append(item)
    _save(items)
    return item


def list_items(status=None):
    items = _load()
    if not items:
        return "📋 暂无工作项。"
    if status and status != "all":
        eng_status = STATUS_MAP.get(status, status)
        if eng_status not in ("todo", "doing", "done"):
            return f"❌ 不支持的状态：{status}（支持：待办/进行中/已完成/全部）"
        items = [i for i in items if i["status"] == eng_status]
        if not items:
            return f"📋 没有「{status}」状态的工作项。"
    lines = ["📋 工作列表："]
    status_order = {"todo": 0, "doing": 1, "done": 2}
    items.sort(key=lambda x: (status_order.get(x["status"], 9), x.get("deadline", "")))
    for i, item in enumerate(items, 1):
        icon = STATUS_ICON.get(item["status"], "📋")
        p = f" [{'🔴高' if item['priority']=='高' else '🟡中' if item['priority']=='中' else '🟢低'}]"
        dl = f" 📅{item['deadline']}" if item.get("deadline") else ""
        lines.append(f"  {i}. {icon}{p}{dl} {item['title']}")
        lines.append(f"     ID: {item['id']}")
    return "\n".join(lines)


def view(item_id):
    items = _load()
    for item in items:
        if item["id"] == item_id:
            icon = STATUS_ICON.get(item["status"], "📋")
            p_icon = "🔴" if item["priority"] == "高" else "🟡" if item["priority"] == "中" else "🟢"
            lines = [
                f"{icon} {item['title']}",
                f"  状态：{STATUS_LABEL.get(item['status'], item['status'])}",
                f"  优先级：{p_icon}{item['priority']}",
            ]
            if item.get("deadline"):
                lines.append(f"  截止：📅 {item['deadline']}")
            if item.get("notes"):
                lines.append(f"  备注：{item['notes']}")
            lines.append(f"  ID：{item['id']}")
            return "\n".join(lines)
    return f"❌ 未找到工作项 ID：{item_id}"


def set_status(item_id, status):
    items = _load()
    for item in items:
        if item["id"] == item_id:
            old = item["status"]
            eng_status = STATUS_MAP.get(status, status)
            item["status"] = eng_status
            _save(items)
            icon = STATUS_ICON.get(eng_status, "📋")
            return f"{icon} {item['title']}：{STATUS_LABEL.get(old, old)} → {STATUS_LABEL.get(eng_status, eng_status)}"
    return f"❌ 未找到工作项 ID：{item_id}"


def set_priority(item_id, priority):
    if priority not in PRIORITIES:
        return f"❌ 不支持：{priority}（支持：{'/'.join(PRIORITIES)}）"
    items = _load()
    for item in items:
        if item["id"] == item_id:
            item["priority"] = priority
            _save(items)
            return f"✅ 已设优先级：{'🔴' if priority=='高' else '🟡' if priority=='中' else '🟢'}{priority}"
    return f"❌ 未找到工作项 ID：{item_id}"


def set_deadline(item_id, deadline):
    items = _load()
    for item in items:
        if item["id"] == item_id:
            item["deadline"] = deadline
            _save(items)
            return f"✅ 已设截止日期：📅 {deadline}"
    return f"❌ 未找到工作项 ID：{item_id}"


def set_notes(item_id, notes):
    items = _load()
    for item in items:
        if item["id"] == item_id:
            item["notes"] = notes
            _save(items)
            return f"✅ 已更新备注。"
    return f"❌ 未找到工作项 ID：{item_id}"


def delete(item_id):
    items = _load()
    new_items = [i for i in items if i["id"] != item_id]
    if len(new_items) == len(items):
        return f"❌ 未找到工作项 ID：{item_id}"
    deleted = [i for i in items if i["id"] == item_id][0]
    _save(new_items)
    return f"✅ 已删除：{deleted['title']}"
