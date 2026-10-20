"""
API 限流中间件。
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, Tuple

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    简单的 API 限流中间件。

    使用令牌桶算法，支持按 IP 地址限流。
    """

    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        """
        初始化限流中间件。

        Args:
            app: FastAPI 应用
            max_requests: 窗口期内最大请求数
            window_seconds: 时间窗口（秒）
        """
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # 存储每个 IP 的请求记录: {ip: [timestamp1, timestamp2, ...]}
        self._requests: Dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端 IP 地址。"""
        # 优先使用 X-Forwarded-For 头（代理场景）
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # 使用 X-Real-IP 头
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 使用客户端 IP
        return request.client.host if request.client else "unknown"

    def _cleanup_old_requests(self, ip: str, now: float) -> None:
        """清理过期的请求记录。"""
        cutoff = now - self.window_seconds
        self._requests[ip] = [t for t in self._requests[ip] if t > cutoff]

    def _is_rate_limited(self, ip: str) -> bool:
        """检查是否触发限流。"""
        now = time.time()
        self._cleanup_old_requests(ip, now)

        if len(self._requests[ip]) >= self.max_requests:
            return True

        self._requests[ip].append(now)
        return False

    def _get_rate_limit_headers(self, ip: str) -> Dict[str, str]:
        """获取限流相关的响应头。"""
        now = time.time()
        self._cleanup_old_requests(ip, now)

        remaining = max(0, self.max_requests - len(self._requests[ip]))
        reset_time = int(now + self.window_seconds)

        return {
            "X-RateLimit-Limit": str(self.max_requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
        }

    async def dispatch(self, request: Request, call_next):
        # 跳过健康检查和静态资源
        if request.url.path in ("/health", "/") or request.url.path.startswith("/static"):
            return await call_next(request)

        ip = self._get_client_ip(request)

        # 检查限流
        if self._is_rate_limited(ip):
            return Response(
                content='{"error": "Too many requests", "detail": "Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
                headers={
                    "Retry-After": str(self.window_seconds),
                    **self._get_rate_limit_headers(ip),
                },
            )

        # 继续处理请求
        response = await call_next(request)

        # 添加限流响应头
        for key, value in self._get_rate_limit_headers(ip).items():
            response.headers[key] = value

        return response
