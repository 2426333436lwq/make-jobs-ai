"""
限流中间件测试。
"""
from __future__ import annotations

import time

import pytest

from app.services.rate_limiter import RateLimitMiddleware


class MockApp:
    """模拟 FastAPI 应用。"""

    async def __call__(self, scope, receive, send):
        pass


class MockRequest:
    """模拟请求对象。"""

    def __init__(self, path="/test", headers=None, client_host="127.0.0.1"):
        self.url = type("URL", (), {"path": path})()
        self.headers = headers or {}
        self.client = type("Client", (), {"host": client_host})()


@pytest.fixture
def rate_limiter():
    return RateLimitMiddleware(MockApp(), max_requests=3, window_seconds=60)


class TestRateLimitMiddleware:
    def test_allows_requests_under_limit(self, rate_limiter):
        """测试未超过限制时允许请求。"""
        request = MockRequest()
        assert rate_limiter._is_rate_limited(request.client.host) is False

    def test_blocks_requests_over_limit(self, rate_limiter):
        """测试超过限制时阻止请求。"""
        ip = "192.168.1.1"
        # 发送 3 个请求
        for _ in range(3):
            rate_limiter._is_rate_limited(ip)

        # 第 4 个请求应该被阻止
        assert rate_limiter._is_rate_limited(ip) is True

    def test_cleanup_old_requests(self, rate_limiter):
        """测试清理过期请求。"""
        ip = "10.0.0.1"
        now = time.time()

        # 添加过期的请求记录
        rate_limiter._requests[ip] = [now - 120, now - 120, now - 120]

        # 清理后应该可以发送新请求
        rate_limiter._cleanup_old_requests(ip, now)
        assert rate_limiter._is_rate_limited(ip) is False

    def test_get_client_ip_from_x_forwarded_for(self, rate_limiter):
        """测试从 X-Forwarded-For 获取 IP。"""
        request = MockRequest(headers={"X-Forwarded-For": "203.0.113.1, 70.41.3.18"})
        ip = rate_limiter._get_client_ip(request)
        assert ip == "203.0.113.1"

    def test_get_client_ip_from_x_real_ip(self, rate_limiter):
        """测试从 X-Real-IP 获取 IP。"""
        request = MockRequest(headers={"X-Real-IP": "198.51.100.1"})
        ip = rate_limiter._get_client_ip(request)
        assert ip == "198.51.100.1"

    def test_get_client_ip_from_client(self, rate_limiter):
        """测试从客户端获取 IP。"""
        request = MockRequest(client_host="10.0.0.100")
        ip = rate_limiter._get_client_ip(request)
        assert ip == "10.0.0.100"
