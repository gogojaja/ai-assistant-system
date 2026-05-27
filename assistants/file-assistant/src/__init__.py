import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

COMMANDS = {
    "查看": {
        "aliases": ["查看", "列表", "打开"],
        "args_count": 1,
        "description": "查看目录内容或预览文件",
        "usage": "查看 <路径>",
        "example": "查看 ~/Documents",
    },
    "搜索": {
        "aliases": ["搜索", "查找", "找文件"],
        "args_count": 1,
        "description": "按文件名搜索文件",
        "usage": "搜索 <文件名关键词>",
        "example": "搜索 report",
    },
    "信息": {
        "aliases": ["信息", "详情", "属性"],
        "args_count": 1,
        "description": "查看文件或目录的详细信息",
        "usage": "信息 <路径>",
        "example": "信息 ~/test.txt",
    },
    "复制": {
        "aliases": ["复制", "拷贝"],
        "args_count": 2,
        "description": "复制文件或目录到目标位置",
        "usage": "复制 <源路径> <目标路径>",
        "example": "复制 ~/a.txt ~/b.txt",
    },
    "移动": {
        "aliases": ["移动", "剪切"],
        "args_count": 2,
        "description": "移动文件或目录到目标位置",
        "usage": "移动 <源路径> <目标路径>",
        "example": "移动 ~/a.txt ~/docs/",
    },
    "重命名": {
        "aliases": ["重命名", "改名"],
        "args_count": 2,
        "description": "重命名文件或目录",
        "usage": "重命名 <路径> <新名称>",
        "example": "重命名 ~/a.txt b.txt",
    },
    "删除": {
        "aliases": ["删除", "移除"],
        "args_count": -1,
        "description": "将文件或空目录移入回收站（支持批量）",
        "usage": "删除 <路径1> [路径2 ...]",
        "example": "删除 ~/tmp.txt ~/old.docx",
    },
    "创建目录": {
        "aliases": ["创建目录", "新建目录", "新建文件夹", "mkdir"],
        "args_count": 1,
        "description": "创建新目录",
        "usage": "创建目录 <路径>",
        "example": "创建目录 ~/newfolder",
    },
    "上传": {
        "aliases": ["上传", "接收文件"],
        "args_count": -1,
        "description": "接收飞书文件并保存到本地（可指定保存路径）",
        "usage": "上传 [保存路径]",
        "example": "上传 ~/Documents",
    },
    "下载": {
        "aliases": ["下载", "保存"],
        "args_count": 1,
        "description": "通过飞书发送文件给你",
        "usage": "下载 <路径>",
        "example": "下载 ~/report.docx",
    },
    "分享": {
        "aliases": ["分享", "发送"],
        "args_count": 1,
        "description": "通过飞书发送文件给对方",
        "usage": "分享 <路径>",
        "example": "分享 ~/photo.jpg",
    },
    "帮助": {
        "aliases": ["帮助", "help", "?", "h"],
        "args_count": 0,
        "description": "显示帮助信息",
        "usage": "帮助",
        "example": "帮助",
    },
}


def _get_canonical_command(verb: str) -> str:
    verb = verb.strip()
    for canonical, info in COMMANDS.items():
        if verb == canonical or verb in info.get("aliases", []):
            return canonical
    return None


def _get_args(text: str) -> list:
    args = []
    parts = text.strip().split()
    i = 0
    while i < len(parts):
        if parts[i].startswith("'") or parts[i].startswith('"'):
            quote = parts[i][0]
            quoted = [parts[i][1:]]
            i += 1
            while i < len(parts) and not parts[i].endswith(quote):
                quoted.append(parts[i])
                i += 1
            if i < len(parts):
                quoted.append(parts[i][:-1])
            args.append(" ".join(quoted))
        else:
            args.append(parts[i])
        i += 1
    return args


def build_help_text() -> str:
    lines = ["📋 4号文件助手 - 可用命令\n"]
    for canonical, info in COMMANDS.items():
        lines.append(f"  {info['usage']}")
        lines.append(f"    {info['description']}")
        if canonical != "帮助":
            lines.append(f"    示例：{info['example']}")
        lines.append("")
    lines.append("💡 直接发送命令即可，无需前缀")
    lines.append("💡 提示：路径支持 ~/ 缩写，路径包含空格请用引号包裹")
    return "\n".join(lines)


def process(message: str, open_id: str = None, feishu_config: dict = None) -> str:
    text = message.strip() if message else ""
    for prefix in ["#4 ", "#file "]:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
            break
    if not text:
        return build_help_text()
    args = _get_args(text)
    verb = args[0] if args else ""
    cmd_args = args[1:] if len(args) > 1 else []
    canonical = _get_canonical_command(verb)
    if canonical is None:
        return (
            f"❌ 未知命令：{verb}\n\n"
            f"可用命令：{'、'.join(COMMANDS.keys())}\n"
            f"请输入 帮助 查看详细用法"
        )
    if canonical == "帮助":
        return build_help_text()
    cmd_info = COMMANDS[canonical]
    expected = cmd_info["args_count"]
    if expected >= 0 and len(cmd_args) != expected:
        if expected == 0:
            return f"❌ 命令「{canonical}」不需要参数，请直接输入 {canonical}"
        return (
            f"❌ 命令「{canonical}」参数数量错误（需要 {expected} 个，实际 {len(cmd_args)} 个）\n\n"
            f"正确格式：{cmd_info['usage']}\n"
            f"示例：{cmd_info['example']}"
        )
    if expected == -1:
        if canonical == "上传" and len(cmd_args) > 1:
            return (
                f"❌ 命令「{canonical}」最多接受 1 个参数（实际 {len(cmd_args)} 个）\n\n"
                f"正确格式：{cmd_info['usage']}\n"
                f"示例：{cmd_info['example']}"
            )
    if canonical in ("查看", "搜索", "信息", "创建目录", "下载", "分享"):
        return _execute_path_command(canonical, cmd_args[0] if cmd_args else None, open_id, feishu_config)
    elif canonical == "删除":
        return _execute_batch_delete(cmd_args, open_id)
    elif canonical in ("复制", "移动"):
        return _execute_dual_path_command(canonical, cmd_args[0], cmd_args[1], open_id)
    elif canonical == "重命名":
        return _execute_rename_command(cmd_args[0], cmd_args[1], open_id)
    elif canonical == "上传":
        if feishu_config and "upload_callback" in feishu_config:
            upload_cb = feishu_config["upload_callback"]
            path_arg = cmd_args[0] if len(cmd_args) > 0 else None
            return upload_cb(open_id, path_arg)
        return "📤 请先发送文件或图片给我，然后输入 上传 保存"
    return build_help_text()


def _execute_path_command(canonical: str, path_arg: str, open_id: str = None, feishu_config: dict = None) -> str:
    from file_manager import cmd_ls, cmd_find, cmd_info, cmd_cat, cmd_mkdir
    from file_transfer import cmd_share
    from security import check_file_operation, resolve_path
    if not path_arg:
        cmd_info = COMMANDS[canonical]
        return f"❌ 命令「{canonical}」缺少路径参数\n正确格式：{cmd_info['usage']}"
    resolved = resolve_path(path_arg)
    if canonical == "搜索":
        allowed_dirs = _get_allowed_dirs()
        search_base = allowed_dirs[0] if allowed_dirs else os.path.expanduser("~")
        return cmd_find(search_base, path_arg)
    if canonical == "查看":
        check = check_file_operation(resolved, "read")
        if not check["valid"]:
            return f"❌ {check['reason']}"
        result = cmd_ls(resolved) if os.path.isdir(resolved) else cmd_cat(resolved)
        result += "\n" + _build_action_hints(resolved)
        return result
    if canonical == "信息":
        check = check_file_operation(resolved, "read")
        if not check["valid"]:
            return f"❌ {check['reason']}"
        result = cmd_info(resolved)
        result += "\n" + _build_action_hints(resolved)
        return result
    if canonical == "删除":
        check = check_file_operation(resolved, "delete")
        if not check["valid"]:
            return f"❌ {check['reason']}"
        return cmd_rm(resolved)
    if canonical == "创建目录":
        check = check_file_operation(resolved, "write")
        if not check["valid"] and check["reason"].startswith("路径不存在"):
            check = {"valid": True, "resolved": resolved}
        if not check["valid"]:
            return f"❌ {check['reason']}"
        return cmd_mkdir(resolved)
    if canonical == "下载":
        check = check_file_operation(resolved, "read")
        if not check["valid"]:
            return f"❌ {check['reason']}"
        return cmd_share(resolved, open_id)
    if canonical == "分享":
        check = check_file_operation(resolved, "read")
        if not check["valid"]:
            return f"❌ {check['reason']}"
        return cmd_share(resolved, open_id)
    return build_help_text()


def _execute_dual_path_command(canonical: str, src: str, dst: str, open_id: str = None) -> str:
    from file_manager import cmd_cp, cmd_mv
    from security import check_file_operation, resolve_path
    src_resolved = resolve_path(src)
    dst_resolved = resolve_path(dst)
    src_check = check_file_operation(src_resolved, "read")
    if not src_check["valid"]:
        return f"❌ 源{src_check['reason']}"
    dst_check = check_file_operation(os.path.dirname(dst_resolved) if not dst_resolved.endswith("/") else dst_resolved, "write") if os.path.exists(os.path.dirname(dst_resolved)) else {"valid": True}
    if isinstance(dst_check, dict) and not dst_check.get("valid", True):
        return f"❌ 目标{dst_check['reason']}"
    if canonical == "复制":
        return cmd_cp(src_resolved, dst_resolved)
    elif canonical == "移动":
        return cmd_mv(src_resolved, dst_resolved)
    return build_help_text()


def _execute_batch_delete(path_args: list, open_id: str = None) -> str:
    from file_manager import cmd_trash
    from security import check_file_operation, resolve_path
    if not path_args:
        return "❌ 请指定要删除的路径\n正确格式：删除 <路径1> [路径2 ...]"
    results = []
    for p in path_args:
        resolved = resolve_path(p)
        check = check_file_operation(resolved, "delete")
        if not check["valid"]:
            results.append(f"❌ {p}：{check['reason']}")
        else:
            results.append(cmd_trash(resolved))
    return "\n".join(results)


def _execute_rename_command(path_arg: str, new_name: str, open_id: str = None) -> str:
    from file_manager import cmd_rename
    from security import check_file_operation, resolve_path
    resolved = resolve_path(path_arg)
    check = check_file_operation(resolved, "rename")
    if not check["valid"]:
        return f"❌ {check['reason']}"
    if "/" in new_name or new_name.strip() != new_name:
        return "❌ 新名称不能包含路径分隔符或首尾空格"
    return cmd_rename(resolved, new_name)


def _build_action_hints(path: str) -> str:
    if os.path.isdir(path):
        hints = [
            "📌 可进行的操作：",
            f"  查看 <子目录名>   进入子目录",
            f"  信息 {_short_path(path)}   查看目录详情",
            f"  创建目录 {_short_path(path)}/<名称>   创建子目录",
            f"  复制 {_short_path(path)} <目标>   复制目录",
            f"  移动 {_short_path(path)} <目标>   移动目录",
            f"  删除 {_short_path(path)}   移入回收站",
            f"  上传 {_short_path(path)}   上传文件到此目录",
        ]
        return "\n" + "\n".join(hints)
    else:
        hints = [
            "📌 可进行的操作：",
            f"  信息 {_short_path(path)}   查看文件详情",
            f"  复制 {_short_path(path)} <目标>   复制文件",
            f"  移动 {_short_path(path)} <目标>   移动文件",
            f"  重命名 {_short_path(path)} <新名称>   重命名",
            f"  删除 {_short_path(path)}   移入回收站",
            f"  下载 {_short_path(path)}   通过飞书获取文件",
            f"  分享 {_short_path(path)}   通过飞书发送文件",
        ]
        return "\n" + "\n".join(hints)


def _short_path(path: str) -> str:
    home = os.path.expanduser("~")
    if path.startswith(home):
        return path.replace(home, "~", 1)
    return path


def _get_allowed_dirs() -> list:
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    config_path = str(project_root / "config" / "whitelist.yaml")
    from security import get_allowed_dirs_from_config
    return get_allowed_dirs_from_config(config_path)
