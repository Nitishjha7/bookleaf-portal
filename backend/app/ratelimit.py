"""Failed-login limiter. Kept in memory, so it is per instance (fine for one Cloud Run
instance; with several instances this would move to Redis or the database)."""
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


class LoginLimiter:
    def __init__(self, max_failures: int = 5, window_seconds: int = 15 * 60):
        self.max_failures = max_failures
        self.window = window_seconds
        self._failures: dict[str, deque] = defaultdict(deque)

    def _recent(self, key: str) -> deque:
        q = self._failures[key]
        cutoff = time.monotonic() - self.window
        while q and q[0] < cutoff:
            q.popleft()
        if not q:
            self._failures.pop(key, None)
        return q

    def check(self, key: str) -> None:
        q = self._recent(key)
        if len(q) >= self.max_failures:
            retry = int(self.window - (time.monotonic() - q[0])) + 1
            raise HTTPException(
                status_code=429,
                detail="Too many failed attempts. Try again later.",
                headers={"Retry-After": str(retry)},
            )

    def record_failure(self, key: str) -> None:
        self._failures[key].append(time.monotonic())

    def reset(self, key: str) -> None:
        self._failures.pop(key, None)


login_limiter = LoginLimiter()


def client_key(request: Request, email: str) -> str:
    # behind Cloud Run the real client is the first X-Forwarded-For entry
    forwarded = request.headers.get("x-forwarded-for", "")
    ip = forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")
    return f"{ip}|{email}"
