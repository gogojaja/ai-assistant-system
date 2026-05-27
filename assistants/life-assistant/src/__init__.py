from .scheduler import add as sched_add, list_items as sched_list, delete as sched_del, search as sched_search
from .health_tracker import record as health_record, report as health_report, TYPES
from .health_analyzer import analyze_trend
from .reminder import check_reminders
from .travel_planner import (
    create as trip_create, list_trips, view as trip_view,
    add_activity, pack_item, toggle_pack, delete as trip_del,
    delete_activity,
)
from .workout_planner import (
    create as wp_create, list_plans, view as wp_view,
    add_exercise, log_workout, history as wp_history, delete as wp_del,
)
from .work_planner import (
    create as work_create, list_items as work_list, view as work_view,
    set_status, set_priority, set_deadline, set_notes, delete as work_del,
)

HELP_TEXT = """🤖 3号AI 生活助手
📅 日程管理：
  #3 schedule add <时间> <事件>  — 创建日程
  #3 schedule list [日期]         — 查看日程
  #3 schedule del <id>            — 删除日程
  #3 schedule search <关键词>     — 搜索日程
🏥 健康管理：
  #3 health record <类型> <数值>  — 记录数据
  #3 health report <日报/周报/月报> — 查看报告
  #3 health trend <类型>          — 趋势分析
🗺️ 旅行规划：
  #3 travel create <目的地> <开始> [结束]  — 创建旅行
  #3 travel list                           — 查看所有旅行
  #3 travel view <id>                      — 查看旅行详情
  #3 travel add <id> <活动>               — 添加行程活动
  #3 travel del_activity <id> <序号>       — 删除活动
  #3 travel pack <id> <物品>               — 添加行李
  #3 travel pack_check <id> <关键词>        — 打包/取消打包
  #3 travel del <id>                        — 删除整个旅行

🏋️ 锻炼规划：
  #3 workout create <名称>                 — 创建锻炼计划
  #3 workout list                          — 查看所有计划
  #3 workout view <id>                     — 查看计划详情
  #3 workout add <id> <动作> <组数>x<次数> — 添加训练项目
  #3 workout log <id> [备注]               — 记录一次训练
  #3 workout history <id>                  — 查看训练历史
  #3 workout del <id>                       — 删除计划
📋 工作规划：
  #3 work create <标题>                    — 创建工作项
  #3 work list [todo/doing/done]           — 查看工作列表
  #3 work view <id>                        — 查看详情
  #3 work start <id>                       — 开始做
  #3 work done <id>                        — 标记完成
  #3 work reopen <id>                      — 重新打开
  #3 work priority <id> <高/中/低>          — 设置优先级
  #3 work deadline <id> <日期>             — 设置截止
  #3 work note <id> <备注>                 — 添加备注
  #3 work del <id>                          — 删除
🗄️ 网页看板：
  #3 dashboard                             — 打开网页看板
❓ #3 help  — 显示此帮助"""


def process(text, open_id="", dashboard_url=""):
    text = text.strip()
    for prefix in ["#3 ", "#life ", "#3", "#life"]:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
            break
    if not text or text == "help":
        return HELP_TEXT
    if text == "dashboard":
        if dashboard_url:
            return f"📊 网页看板已开启：\n{dashboard_url}\n\n建议在手机浏览器或飞书中打开查看。"
        return "📊 网页看板地址未配置，请联系管理员设置 dashboard_url。"

    parts = text.split()
    cmd = parts[0]
    args = parts[1:] if len(parts) > 1 else []

    if cmd == "schedule":
        return _handle_schedule(args)
    elif cmd == "health":
        return _handle_health(args)
    elif cmd == "travel":
        return _handle_travel(args)
    elif cmd == "workout":
        return _handle_workout(args)
    elif cmd == "work":
        return _handle_work(args)
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


def _handle_travel(args):
    if not args:
        return "🗺️ 用法：\n  #3 travel create <目的地> <开始> [结束]\n  #3 travel list\n  #3 travel view <id>\n  #3 travel add <id> <活动>\n  #3 travel del_activity <id> <序号>\n  #3 travel pack <id> <物品>\n  #3 travel pack_check <id> <关键词>\n  #3 travel del <id>"
    sub = args[0]
    rest = args[1:]

    if sub == "create":
        if len(rest) < 2:
            return "❌ 格式：#3 travel create <目的地> <开始日期> [结束日期]"
        dest = rest[0]
        start = rest[1]
        end = rest[2] if len(rest) > 2 else ""
        trip = trip_create(dest, start, end)
        return f"✅ 已创建旅行计划：{trip['destination']}（{trip['start_date']} ~ {trip.get('end_date', '')}）\n  ID：{trip['id']}"

    elif sub == "list":
        return list_trips()

    elif sub == "view":
        if not rest:
            return "❌ 格式：#3 travel view <id>"
        return trip_view(rest[0])

    elif sub == "add":
        if len(rest) < 2:
            return "❌ 格式：#3 travel add <id> <活动描述>"
        return add_activity(rest[0], " ".join(rest[1:]))

    elif sub == "del_activity":
        if len(rest) < 2:
            return "❌ 格式：#3 travel del_activity <id> <序号>"
        try:
            idx = int(rest[1])
        except ValueError:
            return "❌ 序号必须是数字"
        return delete_activity(rest[0], idx)

    elif sub == "pack":
        if len(rest) < 2:
            return "❌ 格式：#3 travel pack <id> <物品>"
        return pack_item(rest[0], " ".join(rest[1:]))

    elif sub == "pack_check":
        if len(rest) < 2:
            return "❌ 格式：#3 travel pack_check <id> <关键词>"
        return toggle_pack(rest[0], " ".join(rest[1:]))

    elif sub == "del":
        if not rest:
            return "❌ 格式：#3 travel del <id>"
        return trip_del(rest[0])

    else:
        return f"❌ 未知子命令：{sub}"


def _handle_workout(args):
    if not args:
        return "🏋️ 用法：\n  #3 workout create <名称>\n  #3 workout list\n  #3 workout view <id>\n  #3 workout add <id> <动作> <组数>x<次数>\n  #3 workout log <id> [备注]\n  #3 workout history <id>\n  #3 workout del <id>"
    sub = args[0]
    rest = args[1:]

    if sub == "create":
        if not rest:
            return "❌ 格式：#3 workout create <名称>"
        plan = wp_create(" ".join(rest))
        return f"✅ 已创建锻炼计划：{plan['name']}\n  ID：{plan['id']}"

    elif sub == "list":
        return list_plans()

    elif sub == "view":
        if not rest:
            return "❌ 格式：#3 workout view <id>"
        return wp_view(rest[0])

    elif sub == "add":
        if len(rest) < 2:
            return "❌ 格式：#3 workout add <id> <动作> <组数>x<次数>\n  示例：#3 workout add abc123 深蹲 3x12"
        # Parse "深蹲 3x12" style
        plan_id = rest[0]
        exercise_str = " ".join(rest[1:])
        # Try to find a "NxM" pattern
        import re
        m = re.search(r'(\d+)x(\d+)', exercise_str)
        if not m:
            return "❌ 格式：#3 workout add <id> <动作> <组数>x<次数>\n  示例：#3 workout add abc123 深蹲 3x12"
        sets, reps = m.group(1), m.group(2)
        name = exercise_str[:m.start()].strip()
        if not name:
            return "❌ 格式：#3 workout add <id> <动作> <组数>x<次数>\n  示例：#3 workout add abc123 深蹲 3x12"
        return add_exercise(plan_id, name, sets, reps)

    elif sub == "log":
        if not rest:
            return "❌ 格式：#3 workout log <id> [备注]"
        note = " ".join(rest[1:]) if len(rest) > 1 else ""
        return log_workout(rest[0], note)

    elif sub == "history":
        if not rest:
            return "❌ 格式：#3 workout history <id>"
        return wp_history(rest[0])

    elif sub == "del":
        if not rest:
            return "❌ 格式：#3 workout del <id>"
        return wp_del(rest[0])

    else:
        return f"❌ 未知子命令：{sub}"


def _handle_work(args):
    if not args:
        return "📋 用法：\n  #3 work create <标题>\n  #3 work list [todo/doing/done]\n  #3 work view <id>\n  #3 work start <id>\n  #3 work done <id>\n  #3 work reopen <id>\n  #3 work priority <id> <高/中/低>\n  #3 work deadline <id> <日期>\n  #3 work note <id> <备注>\n  #3 work del <id>"
    sub = args[0]
    rest = args[1:]

    if sub == "create":
        if not rest:
            return "❌ 格式：#3 work create <标题>"
        item = work_create(" ".join(rest))
        return f"✅ 已创建工作项：{item['title']}（{item['id']}）"

    elif sub == "list":
        status = rest[0] if rest else None
        if status and status not in ("todo", "doing", "done", "all"):
            return "❌ 支持：todo / doing / done / all（留空=全部）"
        return work_list(status)

    elif sub == "view":
        if not rest:
            return "❌ 格式：#3 work view <id>"
        return work_view(rest[0])

    elif sub == "start":
        if not rest:
            return "❌ 格式：#3 work start <id>"
        return set_status(rest[0], "doing")

    elif sub == "done":
        if not rest:
            return "❌ 格式：#3 work done <id>"
        return set_status(rest[0], "done")

    elif sub == "reopen":
        if not rest:
            return "❌ 格式：#3 work reopen <id>"
        return set_status(rest[0], "todo")

    elif sub == "priority":
        if len(rest) < 2:
            return "❌ 格式：#3 work priority <id> <高/中/低>"
        return set_priority(rest[0], rest[1])

    elif sub == "deadline":
        if len(rest) < 2:
            return "❌ 格式：#3 work deadline <id> <日期>"
        return set_deadline(rest[0], rest[1])

    elif sub == "note":
        if len(rest) < 2:
            return "❌ 格式：#3 work note <id> <备注>"
        return set_notes(rest[0], " ".join(rest[1:]))

    elif sub == "del":
        if not rest:
            return "❌ 格式：#3 work del <id>"
        return work_del(rest[0])

    else:
        return f"❌ 未知子命令：{sub}"
