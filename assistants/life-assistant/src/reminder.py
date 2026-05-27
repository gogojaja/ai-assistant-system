from datetime import datetime, timedelta
from . import scheduler

def check_reminders(within_minutes=30):
    upcoming = scheduler.get_upcoming(minutes=within_minutes)
    if not upcoming:
        return None
    lines = ["⏰ 即将开始的日程："]
    for item in upcoming:
        loc = f" 📍{item['location']}" if item.get("location") else ""
        lines.append(f"  {item['time']} {item['title']}{loc}")
    return "\n".join(lines)
