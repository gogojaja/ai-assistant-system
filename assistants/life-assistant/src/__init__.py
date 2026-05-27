from .scheduler import add as sched_add, list_items as sched_list, delete as sched_del, search as sched_search
from .health_tracker import record as health_record, report as health_report, TYPES
from .health_analyzer import analyze_trend
from .reminder import check_reminders

HELP_TEXT = """🤖 3号AI 日程健康助手
📅 日程管理：
  #3 schedule add <时间> <事件>  — 创建日程（时间格式：2026-05-27 14:00）
  #3 schedule list [日期]         — 查看日程（默认全部）
  #3 schedule del <id>            — 删除日程
  #3 schedule search <关键词>     — 搜索日程
🏥 健康管理：
  #3 health record <类型> <数值>  — 记录数据（类型：weight/steps/sleep/heart_rate）
  #3 health report <日报/周报/月报> — 查看报告
  #3 health trend <类型>          — 趋势分析
❓ #3 help  — 显示此帮助"""

def process(text, open_id=""):
    text = text.strip()
    for prefix in ["#3 ", "#life ", "#3", "#life"]:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
            break
    if not text or text == "help":
        return HELP_TEXT

    parts = text.split()
    cmd = parts[0]
    args = parts[1:] if len(parts) > 1 else []

    if cmd == "schedule":
        return _handle_schedule(args)
    elif cmd == "health":
        return _handle_health(args)
    else:
        return f"❌ 未知命令：{cmd}\n\n{HELP_TEXT}"

def _handle_schedule(args):
    if not args:
        return "📋 用法：\n  #3 schedule add <时间> <事件>\n  #3 schedule list [日期]\n  #3 schedule del <id>\n  #3 schedule search <关键词>"
    sub = args[0]
    rest = args[1:]

    if sub == "add":
        if len(rest) < 2:
            return "❌ 格式：#3 schedule add <时间> <事件>\n  示例：#3 schedule add 2026-05-27 14:00 开会"
        time_str = rest[0]
        title = " ".join(rest[1:])
        item = sched_add(title, time_str)
        return f"✅ 已创建日程：\n  [{item['id']}] {item['time']} {item['title']}"

    elif sub == "list":
        date_str = rest[0] if rest else None
        return sched_list(date_str)

    elif sub == "del":
        if not rest:
            return "❌ 格式：#3 schedule del <id>"
        return sched_del(rest[0])

    elif sub == "search":
        if not rest:
            return "❌ 格式：#3 schedule search <关键词>"
        return sched_search(" ".join(rest))

    else:
        return f"❌ 未知子命令：{sub}"

def _handle_health(args):
    if not args:
        return "🏥 用法：\n  #3 health record <类型> <数值>\n  #3 health report <日报/周报/月报>\n  #3 health trend <类型>"
    sub = args[0]
    rest = args[1:]

    if sub == "record":
        if len(rest) < 2:
            return f"❌ 格式：#3 health record <类型> <数值>\n  类型：{', '.join(TYPES.keys())}"
        return health_record(rest[0], rest[1])

    elif sub == "report":
        period = rest[0] if rest else "日报"
        return health_report(period)

    elif sub == "trend":
        if not rest:
            return "❌ 格式：#3 health trend <类型>"
        return analyze_trend(rest[0])

    else:
        return f"❌ 未知子命令：{sub}"
