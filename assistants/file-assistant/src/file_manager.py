import os
import shutil
import stat
import time
import hashlib
import subprocess
from pathlib import Path


def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024 ** 2:.1f} MB"
    else:
        return f"{size_bytes / 1024 ** 3:.2f} GB"


def format_time(timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))


def get_file_type_label(path):
    if os.path.isdir(path):
        return "📁 目录"
    ext = os.path.splitext(path)[1].lower()
    type_map = {
        ".txt": "📄 文本", ".md": "📝 Markdown",
        ".py": "🐍 Python", ".js": "🟨 JavaScript", ".ts": "🔷 TypeScript",
        ".json": "📋 JSON", ".yaml": "📋 YAML", ".yml": "📋 YAML",
        ".xml": "📋 XML", ".csv": "📊 CSV",
        ".jpg": "🖼️ 图片", ".jpeg": "🖼️ 图片", ".png": "🖼️ 图片",
        ".gif": "🖼️ GIF", ".bmp": "🖼️ 图片", ".svg": "🖼️ SVG",
        ".mp3": "🎵 音频", ".wav": "🎵 音频", ".flac": "🎵 音频",
        ".mp4": "🎬 视频", ".mov": "🎬 视频", ".avi": "🎬 视频",
        ".pdf": "📕 PDF", ".doc": "📘 Word", ".docx": "📘 Word",
        ".xls": "📗 Excel", ".xlsx": "📗 Excel",
        ".ppt": "📙 PPT", ".pptx": "📙 PPT",
        ".zip": "📦 压缩包", ".tar": "📦 压缩包", ".gz": "📦 压缩包",
        ".7z": "📦 压缩包", ".rar": "📦 压缩包",
        ".sh": "⚙️ 脚本", ".bat": "⚙️ 脚本",
        ".dmg": "💿 安装包", ".app": "💿 应用",
    }
    return type_map.get(ext, "📄 文件")


def cmd_ls(path):
    if not os.path.isdir(path):
        return f"❌ 路径不是目录：{path}"
    try:
        entries = os.listdir(path)
    except PermissionError:
        return f"❌ 无权访问该目录：{path}"
    entries.sort(key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
    if not entries:
        return f"📂 目录为空：{path}"
    lines = [f"📂 {path}（共 {len(entries)} 项）\n"]
    for name in entries:
        full = os.path.join(path, name)
        try:
            st = os.stat(full)
            size = format_size(st.st_size) if not os.path.isdir(full) else ""
            mtime = format_time(st.st_mtime)
            label = get_file_type_label(full)
            if os.path.isdir(full):
                lines.append(f"  {label}  {name}/")
            else:
                lines.append(f"  {label}  {name}  ({size})  {mtime}")
        except OSError:
            lines.append(f"  ❓  {name}")
    return "\n".join(lines)


def cmd_find(path, name_pattern):
    results = []
    name_lower = name_pattern.lower()
    try:
        for root, dirs, files in os.walk(path):
            try:
                for name in dirs + files:
                    if name_pattern in name or name.lower().find(name_lower) != -1:
                        full = os.path.join(root, name)
                        results.append(full)
            except PermissionError:
                continue
    except PermissionError:
        return f"❌ 无权访问搜索起始目录：{path}"
    if not results:
        return f"🔍 未找到包含「{name_pattern}」的文件"
    lines = [f"🔍 找到 {len(results)} 个匹配结果：\n"]
    limit = 50
    for r in results[:limit]:
        label = get_file_type_label(r)
        try:
            size = format_size(os.path.getsize(r)) if os.path.isfile(r) else ""
            info = f"  {label}  {r}  ({size})" if size else f"  {label}  {r}"
        except OSError:
            info = f"  ❓  {r}"
        lines.append(info)
    if len(results) > limit:
        lines.append(f"\n... 还有 {len(results) - limit} 个结果未显示")
    return "\n".join(lines)


def cmd_info(path):
    if not os.path.exists(path):
        return f"❌ 路径不存在：{path}"
    try:
        st = os.stat(path)
        lines = [f"📋 文件信息：{path}\n"]
        lines.append(f"  类型：{'目录' if os.path.isdir(path) else '文件'}")
        lines.append(f"  大小：{format_size(st.st_size)}")
        lines.append(f"  创建时间：{format_time(st.st_birthtime)}")
        lines.append(f"  修改时间：{format_time(st.st_mtime)}")
        lines.append(f"  访问时间：{format_time(st.st_atime)}")
        lines.append(f"  权限：{stat.filemode(st.st_mode)}")
        if os.path.isfile(path):
            try:
                with open(path, "rb") as f:
                    md5 = hashlib.md5()
                    for chunk in iter(lambda: f.read(8192), b""):
                        md5.update(chunk)
                lines.append(f"  MD5：{md5.hexdigest()}")
            except Exception:
                pass
        if os.path.isdir(path):
            try:
                count = len(os.listdir(path))
                lines.append(f"  子项数：{count}")
            except PermissionError:
                pass
        return "\n".join(lines)
    except PermissionError:
        return f"❌ 无权访问：{path}"


def _get_image_info(path):
    try:
        result = subprocess.run(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", "-g", "space", path],
            capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().split("\n")
        info = {}
        for line in lines:
            if ":" in line:
                key, val = line.split(":", 1)
                info[key.strip()] = val.strip()
        w = info.get("pixelWidth", "?")
        h = info.get("pixelHeight", "?")
        return f"  🖼️ 尺寸：{w} × {h} 像素"
    except Exception:
        return ""


def _get_pdf_info(path):
    try:
        result = subprocess.run(
            ["mdls", "-name", "kMDItemNumberOfPages", "-name", "kMDItemPageHeight", path],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.split("\n"):
            if "kMDItemNumberOfPages" in line:
                pages = line.split("=")[-1].strip()
                return f"  📕 页数：{pages}"
    except Exception:
        return ""
    return ""


def cmd_cat(path, max_lines=200):
    if not os.path.isfile(path):
        return f"❌ 路径不是文件：{path}"
    ext = os.path.splitext(path)[1].lower()
    image_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", ".svg"}
    if ext in image_exts:
        info = _get_image_info(path)
        return f"🖼️ {path}\n{info}\n💡 可使用 下载 {path} 获取原文件"
    if ext == ".pdf":
        info = _get_pdf_info(path)
        return f"📕 {path}\n{info}\n💡 可使用 下载 {path} 获取原文件"
    binary_exts = {".mp3", ".wav", ".flac", ".mp4", ".mov", ".avi",
                   ".zip", ".tar", ".gz", ".7z", ".rar",
                   ".dmg", ".app", ".exe", ".bin",
                   ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}
    if ext in binary_exts:
        return f"❌ 不支持预览二进制文件：{path}\n提示：可使用 信息 <路径> 查看文件信息"
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except PermissionError:
        return f"❌ 无权读取文件：{path}"
    total = len(lines)
    if total == 0:
        return f"📄 文件为空：{path}"
    show_lines = lines[:max_lines]
    result = f"📄 {path}（共 {total} 行）\n\n"
    for i, line in enumerate(show_lines, 1):
        result += f"{i:5d}│ {line}"
    if total > max_lines:
        result += f"\n... 剩余 {total - max_lines} 行未显示"
    return result


def cmd_cp(src, dst):
    if not os.path.exists(src):
        return f"❌ 源路径不存在：{src}"
    try:
        if os.path.isdir(src):
            shutil.copytree(src, dst, symlinks=True)
            return f"✅ 目录已复制：{src} → {dst}"
        else:
            shutil.copy2(src, dst)
            return f"✅ 文件已复制：{src} → {dst}"
    except FileExistsError:
        return f"❌ 目标已存在：{dst}"
    except PermissionError:
        return f"❌ 无权限执行复制操作"
    except Exception as e:
        return f"❌ 复制失败：{str(e)}"


def cmd_mv(src, dst):
    if not os.path.exists(src):
        return f"❌ 源路径不存在：{src}"
    try:
        shutil.move(src, dst)
        return f"✅ 已移动：{src} → {dst}"
    except FileExistsError:
        return f"❌ 目标已存在：{dst}"
    except PermissionError:
        return f"❌ 无权限执行移动操作"
    except Exception as e:
        return f"❌ 移动失败：{str(e)}"


def cmd_rename(path, new_name):
    if not os.path.exists(path):
        return f"❌ 路径不存在：{path}"
    parent = os.path.dirname(path)
    dst = os.path.join(parent, new_name)
    if os.path.exists(dst):
        return f"❌ 目标名称已存在：{new_name}"
    try:
        os.rename(path, dst)
        return f"✅ 已重命名：{os.path.basename(path)} → {new_name}"
    except PermissionError:
        return f"❌ 无权限执行重命名操作"
    except Exception as e:
        return f"❌ 重命名失败：{str(e)}"


def cmd_trash(path):
    if not os.path.exists(path):
        return f"❌ 路径不存在：{path}"
    trash_dir = os.path.expanduser("~/.Trash")
    os.makedirs(trash_dir, exist_ok=True)
    base = os.path.basename(path.rstrip("/"))
    dst = os.path.join(trash_dir, base)
    counter = 1
    name, ext = os.path.splitext(base)
    while os.path.exists(dst):
        dst = os.path.join(trash_dir, f"{name}_{counter}{ext}")
        counter += 1
    try:
        shutil.move(path, dst)
        return f"✅ 已移入回收站：{os.path.basename(path)} → {dst}"
    except PermissionError:
        return f"❌ 无权操作：{path}"
    except OSError as e:
        return f"❌ 操作失败：{str(e)}"


def cmd_mkdir(path):
    if os.path.exists(path):
        return f"❌ 路径已存在：{path}"
    try:
        os.makedirs(path, exist_ok=False)
        return f"✅ 目录已创建：{path}"
    except PermissionError:
        return f"❌ 无权创建目录：{path}"
    except Exception as e:
        return f"❌ 创建目录失败：{str(e)}"
