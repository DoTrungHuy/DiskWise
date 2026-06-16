"""Prompts for structured file classification."""

CLASSIFICATION_SYSTEM_PROMPT = """
你是 DiskWise 的文件分类助手。
你只能返回 JSON，不要返回 Markdown。
你不能要求移动、删除或读取任何文件。
如果信息不足，请降低 confidence。
"""


def build_classification_prompt(
    *,
    file_id: int,
    name: str,
    extension: str,
    size: int,
    content_preview: str | None,
    available_categories: list[str],
) -> str:
    preview = (content_preview or "")[:3000]
    return f"""
请根据文件名、扩展名、大小和内容摘要判断文件分类，并建议安全的新文件名。

必须返回这个 JSON 结构：
{{
  "file_id": {file_id},
  "category": "分类",
  "suggested_name": "建议文件名",
  "confidence": 0.0,
  "reason": "简短原因"
}}

可选分类：{available_categories}

文件信息：
- file_id: {file_id}
- name: {name}
- extension: {extension}
- size: {size}
- content_preview: {preview}
""".strip()
