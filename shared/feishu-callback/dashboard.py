import json
from datetime import date, datetime, timedelta
from pathlib import Path
from flask import Blueprint, request

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "life"

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def _load(filename):
    path = DATA_DIR / filename
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def _base_html(title, body):
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>{title} - 3号AI</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; background:#f5f5f7; color:#1d1d1f; font-size:16px; line-height:1.5; padding:0 0 80px 0; }}
.header {{ background:linear-gradient(135deg,#667eea,#764ba2); color:#fff; padding:16px 16px 14px; position:sticky; top:0; z-index:100; }}
.header h1 {{ font-size:20px; font-weight:600; }}
.header .sub {{ font-size:13px; opacity:.85; margin-top:2px; }}
.nav {{ display:flex; gap:8px; padding:12px 16px; overflow-x:auto; -webkit-overflow-scrolling:touch; scrollbar-width:none; }}
.nav::-webkit-scrollbar {{ display:none; }}
.nav a {{ flex-shrink:0; text-decoration:none; padding:8px 14px; border-radius:20px; font-size:14px; font-weight:500; background:#e8e8ed; color:#1d1d1f; white-space:nowrap; }}
.nav a.active {{ background:#667eea; color:#fff; }}
.nav a:hover {{ opacity:.85; }}
.back {{ display:inline-block; text-decoration:none; color:#667eea; font-size:14px; padding:12px 16px; }}
.back:hover {{ text-decoration:underline; }}
.card {{ background:#fff; margin:12px 16px; border-radius:14px; padding:16px; box-shadow:0 1px 3px rgba(0,0,0,.08); }}
.card-title {{ font-size:15px; font-weight:600; color:#1d1d1f; margin-bottom:10px; display:flex; align-items:center; gap:6px; }}
.stat-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
.stat-card {{ background:#fff; margin:12px 16px; border-radius:14px; padding:16px; box-shadow:0 1px 3px rgba(0,0,0,.08); text-decoration:none; display:block; }}
.stat-card:active {{ transform:scale(.97); }}
.stat-num {{ font-size:28px; font-weight:700; }}
.stat-label {{ font-size:13px; color:#86868b; margin-top:2px; }}
table {{ width:100%; border-collapse:collapse; font-size:14px; }}
th,td {{ text-align:left; padding:10px 0; border-bottom:1px solid #e8e8ed; }}
th {{ font-weight:600; color:#86868b; font-size:12px; text-transform:uppercase; }}
.badge {{ display:inline-block; padding:2px 8px; border-radius:10px; font-size:12px; font-weight:500; }}
.badge-high {{ background:#fee2e2; color:#dc2626; }}
.badge-medium {{ background:#fef3c7; color:#d97706; }}
.badge-low {{ background:#d1fae5; color:#059669; }}
.badge-todo {{ background:#e8e8ed; color:#6b7280; }}
.badge-doing {{ background:#dbeafe; color:#2563eb; }}
.badge-done {{ background:#d1fae5; color:#059669; }}
.badge-active {{ background:#dbeafe; color:#2563eb; }}
.progress {{ background:#e8e8ed; border-radius:10px; height:8px; overflow:hidden; margin:6px 0; }}
.progress-bar {{ height:100%; background:linear-gradient(90deg,#667eea,#764ba2); border-radius:10px; transition:width .3s; }}
.empty {{ text-align:center; padding:40px 16px; color:#86868b; font-size:15px; }}
.empty-icon {{ font-size:48px; margin-bottom:10px; }}
.item-row {{ display:flex; align-items:center; gap:10px; padding:10px 0; border-bottom:1px solid #e8e8ed; }}
.item-row:last-child {{ border:none; }}
.item-icon {{ font-size:18px; }}
.item-body {{ flex:1; min-width:0; }}
.item-title {{ font-size:15px; font-weight:500; }}
.item-meta {{ font-size:12px; color:#86868b; margin-top:1px; }}
.trip-card {{ background:#fff; margin:12px 16px; border-radius:14px; padding:16px; box-shadow:0 1px 3px rgba(0,0,0,.08); }}
.trip-title {{ font-size:17px; font-weight:600; }}
.trip-dates {{ font-size:13px; color:#86868b; margin:4px 0 10px; }}
.act-item {{ font-size:14px; padding:4px 0; }}
.pack-item {{ display:flex; align-items:center; gap:8px; font-size:14px; padding:4px 0; }}
.pack-checked {{ color:#059669; }}
.pack-unchecked {{ color:#9ca3af; }}
.section {{ margin:8px 0; }}
.section-title {{ font-size:14px; font-weight:600; color:#86868b; margin:12px 0 6px; }}
@media (prefers-color-scheme:dark) {{
body {{ background:#1c1c1e; color:#f5f5f7; }}
.card {{ background:#2c2c2e; }}
.stat-card {{ background:#2c2c2e; }}
.nav a {{ background:#3a3a3c; color:#f5f5f7; }}
th,td {{ border-color:#3a3a3c; }}
.badge-todo {{ background:#3a3a3c; color:#d1d5db; }}
.back {{ color:#818cf8; }}
.trip-card {{ background:#2c2c2e; }}
}}
</style>
</head>
<body>
{body}
</body>
</html>"""


def _header(title, subtitle=""):
    return f"""<div class="header">
  <h1>{title}</h1>
  {f'<div class="sub">{subtitle}</div>' if subtitle else ''}
</div>"""


def _nav(active=None):
    items = [
        ("总览", "/dashboard", ""),
        ("日程", "/dashboard/schedule", "schedule"),
        ("健康", "/dashboard/health", "health"),
        ("旅行", "/dashboard/travel", "travel"),
        ("锻炼", "/dashboard/workout", "workout"),
        ("工作", "/dashboard/work", "work"),
    ]
    links = "".join(
        f'<a href="{url}"{" class=\"active\"" if a == active else ""}>{label}</a>'
        for label, url, a in items
    )
    return f'<div class="nav">{links}</div>'


# ─── Routes ───

@dashboard_bp.route("/")
def index():
    schedules = _load("schedules.json")
    health = _load("health.json")
    travels = _load("travels.json")
    workouts = _load("workouts.json")
    works = _load("works.json")

    today = date.today().isoformat()
    upcoming = sum(1 for s in schedules if s.get("time", "").startswith(today))
    health_week = sum(1 for h in health if h.get("date", "") >= (date.today() - timedelta(days=7)).isoformat())
    active_travels = sum(1 for t in travels if t.get("start_date", "") <= today <= (t.get("end_date") or t["start_date"]))
    total_logs = sum(len(p.get("logs", [])) for p in workouts)
    todo_count = sum(1 for w in works if w.get("status") == "todo")
    doing_count = sum(1 for w in works if w.get("status") == "doing")
    done_count = sum(1 for w in works if w.get("status") == "done")

    body = _header("3号AI 生活助手", f"{date.today().isoformat()}")
    body += _nav()
    body += f"""<div class="stat-grid" style="margin:12px 16px;gap:10px;">
  <a href="/dashboard/schedule" class="card" style="text-decoration:none;display:block;">
    <div style="font-size:24px;">📅</div>
    <div class="stat-num">{upcoming}</div>
    <div class="stat-label">今日日程</div>
  </a>
  <a href="/dashboard/health" class="card" style="text-decoration:none;display:block;">
    <div style="font-size:24px;">🏥</div>
    <div class="stat-num">{health_week}</div>
    <div class="stat-label">本周健康</div>
  </a>
  <a href="/dashboard/travel" class="card" style="text-decoration:none;display:block;">
    <div style="font-size:24px;">🗺️</div>
    <div class="stat-num">{active_travels}/{len(travels)}</div>
    <div class="stat-label">进行中/全部旅行</div>
  </a>
  <a href="/dashboard/workout" class="card" style="text-decoration:none;display:block;">
    <div style="font-size:24px;">🏋️</div>
    <div class="stat-num">{len(workouts)}个计划</div>
    <div class="stat-label">共 {total_logs} 次训练</div>
  </a>
  <a href="/dashboard/work" class="card" style="text-decoration:none;display:block;grid-column:1/-1;">
    <div style="font-size:24px;">📋</div>
    <div>
      <span class="badge badge-todo">{todo_count} 待办</span>
      <span class="badge badge-doing">{doing_count} 进行中</span>
      <span class="badge badge-done">{done_count} 已完成</span>
    </div>
  </a>
</div>"""
    return _base_html("总览", body)


@dashboard_bp.route("/schedule")
def schedule_view():
    schedules = _load("schedules.json")
    schedules.sort(key=lambda x: x.get("time", ""))

    rows = ""
    if not schedules:
        body = _header("📅 日程") + _nav("schedule") + """<div class="empty"><div class="empty-icon">📅</div>暂无日程安排。</div>"""
    else:
        current_date = ""
        for s in schedules:
            d = s.get("time", "").split(" ")[0] if " " in s.get("time", "") else s.get("time", "")
            date_header = ""
            if d != current_date:
                current_date = d
                date_header = f'<div style="font-size:14px;font-weight:600;color:#667eea;margin:16px 16px 6px;">{d}</div>'
            time_str = s.get("time", "")
            loc = f" 📍{s['location']}" if s.get("location") else ""
            note = f" 💬{s['notes']}" if s.get("notes") else ""
            rows += f"""<div class="item-row" style="margin:0 16px;">
  <div class="item-icon">📌</div>
  <div class="item-body">
    <div class="item-title">{s['title']}{loc}{note}</div>
    <div class="item-meta">🕐 {time_str}</div>
  </div>
</div>"""
        body = _header("📅 日程", f"{len(schedules)} 项") + _nav("schedule") + date_header + rows

    return _base_html("日程", body)


@dashboard_bp.route("/health")
def health_view():
    health = _load("health.json")
    if not health:
        body = _header("🏥 健康") + _nav("health") + """<div class="empty"><div class="empty-icon">🏥</div>暂无健康数据。</div>"""
    else:
        types = {"weight": "体重(kg)", "steps": "步数", "sleep": "睡眠(h)", "heart_rate": "心率(bpm)"}
        summary = ""
        for t, label in types.items():
            vals = [float(h["value"]) for h in health if h.get("type") == t]
            if vals:
                avg = sum(vals) / len(vals)
                summary += f"""<div class="card"><div class="card-title">{label}</div>
  <div style="display:flex;justify-content:space-between;font-size:14px;">
    <span>平均 <strong>{avg:.1f}</strong></span>
    <span>最高 <strong>{max(vals)}</strong></span>
    <span>最低 <strong>{min(vals)}</strong></span>
    <span>{len(vals)}次</span>
  </div></div>"""
        recent = sorted(health, key=lambda x: x.get("date", ""), reverse=True)[:20]
        rows = ""
        for h in recent:
            label = types.get(h.get("type", ""), h.get("type", ""))
            rows += f"""<tr><td>{h.get('date','')}</td><td>{label}</td><td style="text-align:right;font-weight:600;">{h['value']}</td></tr>"""

        body = _header("🏥 健康", f"{len(health)} 条记录") + _nav("health") + summary
        if rows:
            body += f"""<div class="card"><div class="card-title">最近记录</div>
  <table><thead><tr><th>日期</th><th>类型</th><th>数值</th></tr></thead><tbody>{rows}</tbody></table></div>"""

    return _base_html("健康", body)


@dashboard_bp.route("/travel")
def travel_view():
    travels = _load("travels.json")
    if not travels:
        body = _header("🗺️ 旅行") + _nav("travel") + """<div class="empty"><div class="empty-icon">🗺️</div>暂无旅行计划。</div>"""
    else:
        cards = ""
        today = date.today().isoformat()
        for t in travels:
            is_active = t.get("start_date", "") <= today <= (t.get("end_date") or t["start_date"])
            badge = '<span class="badge badge-active">进行中</span>' if is_active else ""
            dates = f"{t['start_date']} ~ {t['end_date']}" if t.get("end_date") else t["start_date"]
            acts = t.get("activities", [])
            acts_html = ""
            if acts:
                acts_html = """<div class="section"><div class="section-title">📌 行程活动</div>"""
                for a in acts:
                    d = f" [{a.get('date','')}]" if a.get("date") else ""
                    acts_html += f'<div class="act-item">{d} {a["item"]}</div>'
                acts_html += "</div>"

            pack = t.get("packing_list", [])
            pack_html = ""
            if pack:
                checked = sum(1 for p in pack if p.get("checked"))
                pct = int(checked / len(pack) * 100) if pack else 0
                pack_html = f"""<div class="section"><div class="section-title">🧳 行李 {checked}/{len(pack)}</div>
  <div class="progress"><div class="progress-bar" style="width:{pct}%"></div></div>"""
                for p in pack:
                    ck = "✅" if p.get("checked") else "⬜"
                    cls = "pack-checked" if p.get("checked") else "pack-unchecked"
                    pack_html += f'<div class="pack-item"><span>{ck}</span><span class="{cls}">{p["item"]}</span></div>'
                pack_html += "</div>"

            cards += f"""<div class="trip-card">
  <div class="trip-title">{t['destination']} {badge}</div>
  <div class="trip-dates">📅 {dates}</div>
  {acts_html}
  {pack_html}
</div>"""
        body = _header("🗺️ 旅行", f"{len(travels)} 个计划") + _nav("travel") + cards
    return _base_html("旅行", body)


@dashboard_bp.route("/workout")
def workout_view():
    workouts = _load("workouts.json")
    if not workouts:
        body = _header("🏋️ 锻炼") + _nav("workout") + """<div class="empty"><div class="empty-icon">🏋️</div>暂无锻炼计划。</div>"""
    else:
        cards = ""
        for p in workouts:
            exs = p.get("exercises", [])
            ex_html = ""
            if exs:
                ex_html = """<div class="section"><div class="section-title">📋 训练项目</div>"""
                for e in exs:
                    ex_html += f'<div class="act-item">{e["name"]}  {e["sets"]}x{e["reps"]}</div>'
                ex_html += "</div>"
            logs = p.get("logs", [])
            log_html = ""
            if logs:
                recent = sorted(logs, key=lambda x: x["date"], reverse=True)[:5]
                log_html = """<div class="section"><div class="section-title">📅 最近训练</div>"""
                for lr in recent:
                    note = f" — {lr['note']}" if lr.get("note") else ""
                    log_html += f'<div class="act-item">{lr["date"]}{note}</div>'
                log_html += "</div>"

            cards += f"""<div class="trip-card">
  <div class="trip-title">🏋️ {p['name']}</div>
  <div class="trip-dates">训练 {len(logs)} 次</div>
  {ex_html}
  {log_html}
</div>"""
        body = _header("🏋️ 锻炼", f"{len(workouts)} 个计划") + _nav("workout") + cards
    return _base_html("锻炼", body)


@dashboard_bp.route("/work")
def work_view():
    works = _load("works.json")
    if not works:
        body = _header("📋 工作") + _nav("work") + """<div class="empty"><div class="empty-icon">📋</div>暂无工作项。</div>"""
    else:
        cols = {"todo": "📋 待办", "doing": "🔄 进行中", "done": "✅ 已完成"}
        cards_html = {"todo": "", "doing": "", "done": ""}
        priority_order = {"高": 0, "中": 1, "低": 2}
        works.sort(key=lambda x: (priority_order.get(x.get("priority", "中"), 9), x.get("deadline", "")))

        for w in works:
            s = w.get("status", "todo")
            p_badge = f'<span class="badge badge-high">高</span>' if w["priority"] == "高" else f'<span class="badge badge-medium">中</span>' if w["priority"] == "中" else f'<span class="badge badge-low">低</span>'
            dl = f' 📅{w["deadline"]}' if w.get("deadline") else ""
            note = f'<div style="font-size:12px;color:#86868b;margin-top:2px;">{w["notes"]}</div>' if w.get("notes") else ""
            cards_html[s] += f"""<div class="item-row">
  <div class="item-body">
    <div class="item-title">{w['title']}</div>
    <div class="item-meta">{p_badge}{dl}</div>
    {note}
  </div>
</div>"""

        html = ""
        for s, label in cols.items():
            items = cards_html.get(s, "")
            if not items:
                items = """<div style="text-align:center;padding:20px 0;color:#86868b;font-size:14px;">无</div>"""
            html += f"""<div class="card" style="margin-bottom:0;border-radius:14px 14px 0 0;">
  <div class="card-title">{label} ({sum(1 for w in works if w.get('status')==s)})</div>
</div>
<div class="card" style="margin-top:0;border-radius:0 0 14px 14px;margin-bottom:12px;">
  {items}
</div>"""

        body = _header("📋 工作", f"{len(works)} 项") + _nav("work") + html
    return _base_html("工作", body)
