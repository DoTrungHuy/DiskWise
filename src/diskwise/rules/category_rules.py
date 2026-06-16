"""Deterministic file category rules."""

from __future__ import annotations

from typing import Final


CATEGORY_RULES: Final[dict[str, str]] = {
    ".7z": "压缩包",
    ".apk": "安装包",
    ".avi": "视频",
    ".bat": "脚本",
    ".bmp": "图片",
    ".csv": "表格",
    ".doc": "文档",
    ".docx": "文档",
    ".dmg": "系统镜像",
    ".exe": "安装包",
    ".flv": "视频",
    ".gif": "图片",
    ".gz": "压缩包",
    ".heic": "图片",
    ".iso": "系统镜像",
    ".jpeg": "图片",
    ".jpg": "图片",
    ".js": "代码",
    ".json": "代码",
    ".md": "文档",
    ".mkv": "视频",
    ".mov": "视频",
    ".mp3": "音频",
    ".mp4": "视频",
    ".msi": "安装包",
    ".pdf": "PDF",
    ".png": "图片",
    ".ppt": "演示文稿",
    ".pptx": "演示文稿",
    ".ps1": "脚本",
    ".py": "代码",
    ".rar": "压缩包",
    ".sh": "脚本",
    ".tar": "压缩包",
    ".ts": "代码",
    ".txt": "文档",
    ".wav": "音频",
    ".webp": "图片",
    ".xls": "表格",
    ".xlsx": "表格",
    ".xml": "代码",
    ".yaml": "代码",
    ".yml": "代码",
    ".zip": "压缩包",
}

TEXT_LIKE_EXTENSIONS: Final[set[str]] = {
    ".bat",
    ".csv",
    ".ini",
    ".js",
    ".json",
    ".log",
    ".md",
    ".ps1",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}

DOCUMENT_EXTENSIONS: Final[set[str]] = {
    ".doc",
    ".docx",
    ".pdf",
    ".ppt",
    ".pptx",
    ".xls",
    ".xlsx",
}

IMAGE_EXTENSIONS: Final[set[str]] = {
    ".bmp",
    ".gif",
    ".heic",
    ".jpeg",
    ".jpg",
    ".png",
    ".webp",
}
