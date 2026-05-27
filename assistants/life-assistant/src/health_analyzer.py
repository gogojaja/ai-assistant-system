from datetime import datetime, timedelta, date
from . import health_tracker

TYPES_LABELS = {"weight": "体重", "steps": "步数", "sleep": "睡眠", "heart_rate": "心率"}

def analyze_trend(data_type, days=30):
    if data_type not in TYPES_LABELS:
        return f"❌ 不支持的类型：{data_type}"
    items = health_tracker._load()
    start = (date.today() - timedelta(days=days)).isoformat()
    filtered = sorted(
        [i for i in items if i["type"] == data_type and i["date"] >= start],
        key=lambda x: x["date"]
    )
    if len(filtered) < 2:
        return f"📈 {TYPES_LABELS[data_type]}：数据不足（需至少 2 条记录）"
    vals = [float(i["value"]) for i in filtered]
    trend = "上升" if vals[-1] > vals[0] else "下降" if vals[-1] < vals[0] else "持平"
    return (
        f"📈 {TYPES_LABELS[data_type]}趋势分析（近{days}天，{len(filtered)}条记录）：\n"
        f"  当前 {vals[-1]:.1f}，平均 {sum(vals)/len(vals):.1f}\n"
        f"  最高 {max(vals):.1f}，最低 {min(vals):.1f}\n"
        f"  趋势：{trend}"
    )
