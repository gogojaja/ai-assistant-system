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

HELP_TEXT = """🤖 生活助手
📅 日程管理：
  日程 添加 <时间> <事件>           — 创建日程
  日程 列表 [日期]                  — 查看日程
  日程 删除 <id>                    — 删除日程
  日程 搜索 <关键词>                — 搜索日程
🏥 健康管理：
  健康 记录 <类型> <数值>           — 记录数据
  健康 报告 <日报/周报/月报>        — 查看报告
  健康 趋势 <类型>                  — 趋势分析
🗺️ 旅行规划：
  旅行 创建 <目的地> <开始> [结束]  — 创建旅行
  旅行 列表                         — 查看所有旅行
  旅行 查看 <id>                    — 查看旅行详情
  旅行 添加 <id> <活动>             — 添加行程活动
  旅行 删除活动 <id> <序号>         — 删除活动
  旅行 行李 <id> <物品>             — 添加行李
  旅行 打包 <id> <关键词>            — 打包/取消打包
  旅行 删除 <id>                    — 删除整个旅行
🏋️ 锻炼规划：
  锻炼 创建 <名称>                  — 创建锻炼计划
  锻炼 列表                         — 查看所有计划
  锻炼 查看 <id>                    — 查看计划详情
  锻炼 添加 <id> <动作> <组数>x<次数> — 添加训练项目
  锻炼 记录 <id> [备注]             — 记录一次训练
  锻炼 历史 <id>                    — 查看训练历史
  锻炼 删除 <id>                    — 删除计划
📋 工作规划：
  工作 创建 <标题>                  — 创建工作项
  工作 列表 [待办/进行中/已完成]    — 查看工作列表
  工作 查看 <id>                    — 查看详情
  工作 开始 <id>                    — 开始做
  工作 完成 <id>                    — 标记完成
  工作 重开 <id>                    — 重新打开
  工作 优先级 <id> <高/中/低>       — 设置优先级
  工作 截止 <id> <日期>             — 设置截止
  工作 备注 <id> <备注>             — 添加备注
  工作 删除 <id>                    — 删除
🗄️ 网页看板：
  看板                              — 打开网页看板
❓ 帮助   — 显示此帮助"""


def process(text, open_id="", dashboard_url=""):
    text = text.strip()
    if not text or text == "帮助":
        return HELP_TEXT
    if text == "看板":
        if dashboard_url:
            return f"📊 网页看板已开启：\n{dashboard_url}\n\n建议在手机浏览器或飞书中打开查看。"
        return "📊 网页看板地址未配置，请联系管理员设置 dashboard_url。"

    parts = text.split()
    cmd = parts[0]
    args = parts[1:] if len(parts) > 1 else []

    if cmd == "日程":
        return _handle_schedule(args)
    elif cmd == "健康":
        return _handle_health(args)
    elif cmd == "旅行":
        return _handle_travel(args)
    elif cmd == "锻炼":
        return _handle_workout(args)
    elif cmd == "工作":
        return _handle_work(args)
    else:
        return f"❌ 未知命令：{cmd}\n\n{HELP_TEXT}"


def _handle_schedule(args):
    if not args:
        return "📋 用法：\n  日程 添加 <时间> <事件>\n  日程 列表 [日期]\n  日程 删除 <id>\n  日程 搜索 <关键词>"
    sub = args[0]
    rest = args[1:]

    if sub in ("添加", "add"):
        if len(rest) < 2:
            return "❌ 格式：日程 添加 <时间> <事件>\n  示例：日程 添加 2026-05-27 14:00 开会"
        time_str = rest[0]
        title = " ".join(rest[1:])
        item = sched_add(title, time_str)
        return f"✅ 已创建日程：\n  [{item['id']}] {item['time']} {item['title']}"

    elif sub in ("列表", "list"):
        date_str = rest[0] if rest else None
        return sched_list(date_str)

    elif sub in ("删除", "del"):
        if not rest:
            return "❌ 格式：日程 删除 <id>"
        return sched_del(rest[0])

    elif sub in ("搜索", "search"):
        if not rest:
            return "❌ 格式：日程 搜索 <关键词>"
        return sched_search(" ".join(rest))

    else:
        return f"❌ 未知子命令：{sub}"


def _handle_health(args):
    if not args:
        return "🏥 用法：\n  健康 记录 <类型> <数值>\n  健康 报告 <日报/周报/月报>\n  健康 趋势 <类型>"
    sub = args[0]
    rest = args[1:]

    if sub in ("记录", "record"):
        if len(rest) < 2:
            return f"❌ 格式：健康 记录 <类型> <数值>\n  类型：{', '.join(TYPES.keys())}"
        return health_record(rest[0], rest[1])

    elif sub in ("报告", "report"):
        period = rest[0] if rest else "日报"
        return health_report(period)

    elif sub in ("趋势", "trend"):
        if not rest:
            return "❌ 格式：健康 趋势 <类型>"
        return analyze_trend(rest[0])

    else:
        return f"❌ 未知子命令：{sub}"


def _handle_travel(args):
    if not args:
        return "🗺️ 用法：\n  旅行 创建 <目的地> <开始> [结束]\n  旅行 列表\n  旅行 查看 <id>\n  旅行 添加 <id> <活动>\n  旅行 删除活动 <id> <序号>\n  旅行 行李 <id> <物品>\n  旅行 打包 <id> <关键词>\n  旅行 删除 <id>"
    sub = args[0]
    rest = args[1:]

    if sub in ("创建", "create"):
        if len(rest) < 2:
            return "❌ 格式：旅行 创建 <目的地> <开始日期> [结束日期]"
        dest = rest[0]
        start = rest[1]
        end = rest[2] if len(rest) > 2 else ""
        trip = trip_create(dest, start, end)
        return f"✅ 已创建旅行计划：{trip['destination']}（{trip['start_date']} ~ {trip.get('end_date', '')}）\n  ID：{trip['id']}"

    elif sub in ("列表", "list"):
        return list_trips()

    elif sub in ("查看", "view"):
        if not rest:
            return "❌ 格式：旅行 查看 <id>"
        return trip_view(rest[0])

    elif sub in ("添加", "add"):
        if len(rest) < 2:
            return "❌ 格式：旅行 添加 <id> <活动描述>"
        return add_activity(rest[0], " ".join(rest[1:]))

    elif sub in ("删除活动", "del_activity"):
        if len(rest) < 2:
            return "❌ 格式：旅行 删除活动 <id> <序号>"
        try:
            idx = int(rest[1])
        except ValueError:
            return "❌ 序号必须是数字"
        return delete_activity(rest[0], idx)

    elif sub in ("行李", "pack"):
        if len(rest) < 2:
            return "❌ 格式：旅行 行李 <id> <物品>"
        return pack_item(rest[0], " ".join(rest[1:]))

    elif sub in ("打包", "pack_check"):
        if len(rest) < 2:
            return "❌ 格式：旅行 打包 <id> <关键词>"
        return toggle_pack(rest[0], " ".join(rest[1:]))

    elif sub in ("删除", "del"):
        if not rest:
            return "❌ 格式：旅行 删除 <id>"
        return trip_del(rest[0])

    else:
        return f"❌ 未知子命令：{sub}"


def _handle_workout(args):
    if not args:
        return "🏋️ 用法：\n  锻炼 创建 <名称>\n  锻炼 列表\n  锻炼 查看 <id>\n  锻炼 添加 <id> <动作> <组数>x<次数>\n  锻炼 记录 <id> [备注]\n  锻炼 历史 <id>\n  锻炼 删除 <id>"
    sub = args[0]
    rest = args[1:]

    if sub in ("创建", "create"):
        if not rest:
            return "❌ 格式：锻炼 创建 <名称>"
        plan = wp_create(" ".join(rest))
        return f"✅ 已创建锻炼计划：{plan['name']}\n  ID：{plan['id']}"

    elif sub in ("列表", "list"):
        return list_plans()

    elif sub in ("查看", "view"):
        if not rest:
            return "❌ 格式：锻炼 查看 <id>"
        return wp_view(rest[0])

    elif sub in ("添加", "add"):
        if len(rest) < 2:
            return "❌ 格式：锻炼 添加 <id> <动作> <组数>x<次数>\n  示例：锻炼 添加 abc123 深蹲 3x12"
        plan_id = rest[0]
        exercise_str = " ".join(rest[1:])
        import re
        m = re.search(r'(\d+)x(\d+)', exercise_str)
        if not m:
            return "❌ 格式：锻炼 添加 <id> <动作> <组数>x<次数>\n  示例：锻炼 添加 abc123 深蹲 3x12"
        sets, reps = m.group(1), m.group(2)
        name = exercise_str[:m.start()].strip()
        if not name:
            return "❌ 格式：锻炼 添加 <id> <动作> <组数>x<次数>\n  示例：锻炼 添加 abc123 深蹲 3x12"
        return add_exercise(plan_id, name, sets, reps)

    elif sub in ("记录", "log"):
        if not rest:
            return "❌ 格式：锻炼 记录 <id> [备注]"
        note = " ".join(rest[1:]) if len(rest) > 1 else ""
        return log_workout(rest[0], note)

    elif sub in ("历史", "history"):
        if not rest:
            return "❌ 格式：锻炼 历史 <id>"
        return wp_history(rest[0])

    elif sub in ("删除", "del"):
        if not rest:
            return "❌ 格式：锻炼 删除 <id>"
        return wp_del(rest[0])

    else:
        return f"❌ 未知子命令：{sub}"


def _handle_work(args):
    if not args:
        return "📋 用法：\n  工作 创建 <标题>\n  工作 列表 [待办/进行中/已完成]\n  工作 查看 <id>\n  工作 开始 <id>\n  工作 完成 <id>\n  工作 重开 <id>\n  工作 优先级 <id> <高/中/低>\n  工作 截止 <id> <日期>\n  工作 备注 <id> <备注>\n  工作 删除 <id>"
    sub = args[0]
    rest = args[1:]

    if sub in ("创建", "create"):
        if not rest:
            return "❌ 格式：工作 创建 <标题>"
        item = work_create(" ".join(rest))
        return f"✅ 已创建工作项：{item['title']}（{item['id']}）"

    elif sub in ("列表", "list"):
        status = rest[0] if rest else None
        status_map = {"待办": "todo", "进行中": "doing", "已完成": "done", "全部": "all",
                      "todo": "todo", "doing": "doing", "done": "done", "all": "all"}
        if status and status not in status_map:
            return "❌ 支持：待办 / 进行中 / 已完成 / 全部（留空=全部）"
        return work_list(status_map.get(status, status))

    elif sub in ("查看", "view"):
        if not rest:
            return "❌ 格式：工作 查看 <id>"
        return work_view(rest[0])

    elif sub in ("开始", "start"):
        if not rest:
            return "❌ 格式：工作 开始 <id>"
        return set_status(rest[0], "doing")

    elif sub in ("完成", "done"):
        if not rest:
            return "❌ 格式：工作 完成 <id>"
        return set_status(rest[0], "done")

    elif sub in ("重开", "reopen"):
        if not rest:
            return "❌ 格式：工作 重开 <id>"
        return set_status(rest[0], "todo")

    elif sub in ("优先级", "priority"):
        if len(rest) < 2:
            return "❌ 格式：工作 优先级 <id> <高/中/低>"
        return set_priority(rest[0], rest[1])

    elif sub in ("截止", "deadline"):
        if len(rest) < 2:
            return "❌ 格式：工作 截止 <id> <日期>"
        return set_deadline(rest[0], rest[1])

    elif sub in ("备注", "note"):
        if len(rest) < 2:
            return "❌ 格式：工作 备注 <id> <备注>"
        return set_notes(rest[0], " ".join(rest[1:]))

    elif sub in ("删除", "del"):
        if not rest:
            return "❌ 格式：工作 删除 <id>"
        return work_del(rest[0])

    else:
        return f"❌ 未知子命令：{sub}"
