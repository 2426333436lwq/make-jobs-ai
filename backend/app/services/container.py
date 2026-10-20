"""
依赖注入服务定位器。

提供全局可用的服务实例，支持测试时替换。
"""
from __future__ import annotations

from typing import Optional

# 延迟导入避免循环依赖
_claude_service_instance = None


def get_claude_service():
    """获取 ClaudeService 单例（懒初始化）。"""
    global _claude_service_instance
    if _claude_service_instance is None:
        from app.services.claude_service import ClaudeService
        _claude_service_instance = ClaudeService()
    return _claude_service_instance


def set_claude_service(service) -> None:
    """替换 ClaudeService 实例（用于测试或重新初始化）。"""
    global _claude_service_instance
    _claude_service_instance = service


def reset_claude_service() -> None:
    """重置 ClaudeService 实例。"""
    global _claude_service_instance
    _claude_service_instance = None
