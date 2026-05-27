"""
模块名称：backup_manager
功能描述：5号AI 系统管理助理 — 备份管理（手动触发备份/查看备份列表/还原）
对外接口：
    - cmd_backup_now(): 触发手动备份
    - cmd_backup_list(): 查看可用备份列表
    - cmd_backup_restore(id): 从指定备份还原
依赖：
    - 标准库：subprocess, pathlib, logging, glob
    - 第三方：无
    - 项目内：无
版本：v1.0
更新记录：
    - 2026-05-26: 初始创建
"""
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BACKUP_DIR = PROJECT_ROOT / "backups"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


def cmd_backup_now() -> str:
    backup_script = SCRIPTS_DIR / "daily_backup.sh"
    if backup_script.exists():
        try:
            result = subprocess.run(
                ["bash", str(backup_script)],
                capture_output=True, text=True, timeout=120
            )
            output = result.stdout.strip()
            if result.returncode == 0:
                latest = _get_latest_backup()
                if latest:
                    return f"✅ 备份完成\n最新备份: {latest.name}"
                return f"✅ 备份脚本执行成功\n{output}"
            else:
                return f"❌ 备份失败:\n{result.stderr.strip()}"
        except subprocess.TimeoutExpired:
            return "❌ 备份超时（120秒）"
        except Exception as e:
            return f"❌ 备份异常: {e}"
    else:
        return f"❌ 备份脚本不存在: {backup_script}"


def cmd_backup_list() -> str:
    if not BACKUP_DIR.exists() or not BACKUP_DIR.is_dir():
        return "备份目录不存在"

    backups = sorted(BACKUP_DIR.glob("backup_*.tar.gz"), reverse=True)
    if not backups:
        return "暂无可用备份"

    lines = [f"====== 可用备份 (共 {len(backups)} 个) ======"]
    for i, backup in enumerate(backups, 1):
        size_mb = backup.stat().st_size / (1024 * 1024)
        mod_time = backup.stat().st_mtime
        from datetime import datetime
        time_str = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"  [{i}] {backup.name}  ({size_mb:.1f}MB, {time_str})")
    lines.append("")
    lines.append("还原: #5 backup restore <ID>")
    return "\n".join(lines)


def cmd_backup_restore(id_str: str) -> str:
    if not BACKUP_DIR.exists():
        return "备份目录不存在"

    backups = sorted(BACKUP_DIR.glob("backup_*.tar.gz"), reverse=True)
    if not backups:
        return "暂无可用备份"

    try:
        idx = int(id_str) - 1
        if idx < 0 or idx >= len(backups):
            return f"无效编号: {id_str}，可用范围: 1-{len(backups)}"
    except ValueError:
        return f"无效编号: {id_str}，请输入数字"

    target = backups[idx]
    restore_script = SCRIPTS_DIR / "restore.sh"
    if not restore_script.exists():
        return f"❌ 还原脚本不存在: {restore_script}\n请手动还原:\n  tar -xzf {target} -C /"

    return (
        f"⚠️ 确认还原 {target.name}？\n"
        f"还原操作会:\n"
        f"  1. 停止所有服务\n"
        f"  2. 备份当前环境\n"
        f"  3. 从备份文件还原\n"
        f"\n请手动执行:\n"
        f"  bash {restore_script}\n"
        f"然后选择备份文件 {target.name}"
    )


def _get_latest_backup():
    if not BACKUP_DIR.exists():
        return None
    backups = sorted(BACKUP_DIR.glob("backup_*.tar.gz"), reverse=True)
    return backups[0] if backups else None
