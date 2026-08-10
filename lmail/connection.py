"""
SMTP 连接池管理。
"""

from __future__ import annotations

import logging
import smtplib
import ssl
import threading
from typing import Any

from lmail.exceptions import ConnectionError as LConnectionError

logger = logging.getLogger("lmail")


class ConnectionPool:
    """SMTP 连接池。

    复用 SMTP 连接，减少握手开销。

    典型用法：
        pool = ConnectionPool(
            host="smtp.example.com",
            port=587,
            use_tls=True,
            max_connections=5,
        )
        conn = pool.get()
        # 使用连接...
        pool.release(conn)
    """

    def __init__(
        self,
        host: str,
        port: int = 587,
        use_tls: bool = True,
        use_ssl: bool = False,
        timeout: float = 30.0,
        max_connections: int = 5,
    ) -> None:
        """初始化连接池。

        Args:
            host: SMTP 服务器地址。
            port: SMTP 服务器端口。
            use_tls: 是否使用 STARTTLS。
            use_ssl: 是否使用 SSL（SMTPS）。
            timeout: 连接超时（秒）。
            max_connections: 最大连接数。
        """
        self._host = host
        self._port = port
        self._use_tls = use_tls
        self._use_ssl = use_ssl
        self._timeout = timeout
        self._max_connections = max_connections

        self._pool: list[smtplib.SMTP] = []
        self._lock = threading.Lock()
        self._created = 0

    def get(self) -> smtplib.SMTP:
        """获取连接。

        Returns:
            SMTP 连接对象。

        Raises:
            ConnectionError: 连接失败。
        """
        with self._lock:
            # 尝试从池中获取
            while self._pool:
                conn = self._pool.pop()
                try:
                    conn.noop()  # 检查连接是否存活
                    return conn
                except Exception:
                    self._created -= 1
                    continue

            # 创建新连接
            if self._created >= self._max_connections:
                # 等待连接释放（简单阻塞）
                self._lock.release()
                try:
                    import time
                    time.sleep(0.1)
                finally:
                    self._lock.acquire()
                return self.get()

            try:
                conn = self._create_connection()
                self._created += 1
                return conn
            except Exception as e:
                raise LConnectionError(f"创建 SMTP 连接失败: {e}", original=e) from e

    def release(self, conn: smtplib.SMTP) -> None:
        """释放连接回池。

        Args:
            conn: SMTP 连接对象。
        """
        with self._lock:
            if len(self._pool) < self._max_connections:
                try:
                    conn.noop()  # 检查连接是否可用
                    self._pool.append(conn)
                except Exception:
                    self._close_connection(conn)
                    self._created -= 1
            else:
                self._close_connection(conn)
                self._created -= 1

    def close_all(self) -> None:
        """关闭所有连接。"""
        with self._lock:
            for conn in self._pool:
                self._close_connection(conn)
            self._pool.clear()
            self._created = 0

    def _create_connection(self) -> smtplib.SMTP:
        """创建新的 SMTP 连接。"""
        try:
            if self._use_ssl:
                context = ssl.create_default_context()
                conn = smtplib.SMTP_SSL(
                    self._host,
                    self._port,
                    timeout=self._timeout,
                    context=context,
                )
            else:
                conn = smtplib.SMTP(
                    self._host,
                    self._port,
                    timeout=self._timeout,
                )
                if self._use_tls:
                    context = ssl.create_default_context()
                    conn.starttls(context=context)

            conn.set_debuglevel(0)
            return conn

        except smtplib.SMTPException as e:
            raise LConnectionError(f"SMTP 连接失败: {e}", original=e) from e
        except Exception as e:
            raise LConnectionError(f"连接失败: {e}", original=e) from e

    def _close_connection(self, conn: smtplib.SMTP) -> None:
        """安全关闭连接。"""
        try:
            conn.quit()
        except Exception:
            try:
                conn.close()
            except Exception:
                pass

    @property
    def size(self) -> int:
        """当前池中可用连接数。"""
        return len(self._pool)

    @property
    def created(self) -> int:
        """已创建的连接总数。"""
        return self._created

    def __repr__(self) -> str:
        return (
            f"ConnectionPool(host={self._host!r}, port={self._port}, "
            f"pool_size={self.size}, created={self._created})"
        )
