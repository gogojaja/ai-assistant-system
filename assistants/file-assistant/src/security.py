import os
import stat
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

SENSITIVE_PATTERNS = [
    "/etc",
    "/var",
    "/System",
    "/Library",
    "/.Trash",
    "/.Spotlight-V100",
    "/.fseventsd",
    "/dev",
    "/proc",
    "/sys",
    "/private/etc",
    "/private/var",
]

SENSITIVE_DIR_NAMES = [
    ".ssh",
    ".gnupg",
    ".aws",
    ".kube",
    ".config",
    ".docker",
    ".git",
    ".svn",
    ".env",
    "venv",
    "__pycache__",
    "node_modules",
]

DEFAULT_ALLOWED_PATHS = [".", ".."]

DEFAULT_DENIED_PATTERNS = [
    "*/venv/*",
    "*/.git/*",
    "*/__pycache__/*",
    "*/node_modules/*",
]


def _resolve_allowed_dir(path: str) -> str:
    if path.startswith("~"):
        return os.path.expanduser(path)
    if not path.startswith("/"):
        return os.path.abspath(os.path.join(str(PROJECT_ROOT), path))
    return path


def resolve_path(raw_path: str) -> str:
    raw_path = raw_path.strip().strip("'\"")
    if raw_path.startswith("~"):
        raw_path = os.path.expanduser(raw_path)
    elif not raw_path.startswith("/"):
        raw_path = os.path.join(str(PROJECT_ROOT), raw_path)
    return os.path.abspath(raw_path)


def is_sensitive_path(path: str) -> bool:
    resolved = resolve_path(path)
    for pattern in SENSITIVE_PATTERNS:
        if resolved.startswith(pattern):
            return True
    parts = Path(resolved).parts
    for part in parts:
        if part in SENSITIVE_DIR_NAMES:
            return True
    return False


def is_symlink_outside(path: str, allowed_dirs: list) -> bool:
    try:
        if os.path.islink(path):
            target = os.path.realpath(path)
            for adir in allowed_dirs:
                if target.startswith(adir):
                    return False
            return True
    except Exception:
        return True
    return False


def validate_path(path: str, allowed_dirs: list = None) -> dict:
    if allowed_dirs is None:
        allowed_dirs = [_resolve_allowed_dir(p) for p in DEFAULT_ALLOWED_PATHS]
    resolved = resolve_path(path)
    if not os.path.exists(resolved):
        return {"valid": False, "reason": f"路径不存在：{path}", "resolved": resolved}
    if is_sensitive_path(resolved):
        return {"valid": False, "reason": f"路径包含敏感目录，不允许访问：{path}", "resolved": resolved}
    allowed = False
    for adir in allowed_dirs:
        if resolved.startswith(adir):
            allowed = True
            break
    if not allowed:
        return {"valid": False, "reason": f"路径不在允许访问范围内：{path}", "resolved": resolved}
    if is_symlink_outside(resolved, allowed_dirs):
        return {"valid": False, "reason": f"路径包含指向外部的符号链接，已拦截：{path}", "resolved": resolved}
    return {"valid": True, "reason": "ok", "resolved": resolved}


def check_file_operation(path: str, operation: str, allowed_dirs: list = None) -> dict:
    result = validate_path(path, allowed_dirs)
    if not result["valid"]:
        return result
    resolved = result["resolved"]
    if operation in ("delete", "move", "rename") and not os.access(os.path.dirname(resolved), os.W_OK):
        return {"valid": False, "reason": f"无写入权限：{os.path.dirname(path)}", "resolved": resolved}
    if operation == "read" and not os.access(resolved, os.R_OK):
        return {"valid": False, "reason": f"无读取权限：{path}", "resolved": resolved}
    if operation == "write" and not os.access(os.path.dirname(resolved), os.W_OK):
        return {"valid": False, "reason": f"无写入权限：{os.path.dirname(path)}", "resolved": resolved}
    return {"valid": True, "reason": "ok", "resolved": resolved}


def get_allowed_dirs_from_config(config_path: str = None) -> list:
    if config_path and os.path.exists(config_path):
        try:
            import yaml
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            file_cfg = cfg.get("assistants", {}).get("file", {})
            allowed = file_cfg.get("allowed_paths", DEFAULT_ALLOWED_PATHS)
            return [_resolve_allowed_dir(p) for p in allowed]
        except Exception:
            pass
    return [_resolve_allowed_dir(p) for p in DEFAULT_ALLOWED_PATHS]
