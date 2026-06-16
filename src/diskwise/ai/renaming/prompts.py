"""Prompts for safe filename suggestions."""

RENAMING_SYSTEM_PROMPT = """
你是 DiskWise 的文件命名助手。
只返回 JSON，不要返回 Markdown。
文件名不能包含 Windows 禁止字符：< > : " / \\ | ? *
"""


def build_renaming_prompt(
    *,
    current_name: str,
    category: str | None,
    content_preview: str | None,
) -> str:
    return f"""
请给这个文件生成一个简短、清晰、安全的新文件名，保留原扩展名含义。

必须返回：
{{"suggested_name": "新文件名", "reason": "原因"}}

当前文件名：{current_name}
分类：{category or "未知"}
内容摘要：{(content_preview or "")[:3000]}
""".strip()
