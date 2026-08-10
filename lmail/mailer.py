"""
邮件发送器实现。

提供简洁的 API 发送邮件，支持连接池、认证、HTML/附件。
"""

from __future__ import annotations

import logging
import smtplib
from pathlib import Path
from typing import Any

from lmail.connection import ConnectionPool
from lmail.exceptions import (
    AuthenticationError,
    MailError,
    SMTPError,
)
from lmail.message import Message

logger = logging.getLogger("lmail")


class Mailer:
    """邮件发送器。

    特性：
        - 连接池复用
        - 链式 API 构建邮件
        - 支持 HTML/纯文本/附件
        - 自动认证

    典型用法：
        mailer = Mailer(
            host="smtp.example.com",
            port=587,
            username="user",
            password="pass",
            use_tls=True,
        )

        mailer.send(
            to="recipient@example.com",
            subject="测试",
            html="<h1>你好!</h1>",
        )
    """

    def __init__(
        self,
        host: str,
        port: int = 587,
        username: str = "",
        password: str = "",
        use_tls: bool = True,
        use_ssl: bool = False,
        timeout: float = 30.0,
        pool_size: int = 5,
        from_address: str = "",
        from_name: str = "",
    ) -> None:
        """初始化邮件发送器。

        Args:
            host: SMTP 服务器地址。
            port: SMTP 服务器端口。
            username: 登录用户名。
            password: 登录密码。
            use_tls: 是否使用 STARTTLS。
            use_ssl: 是否使用 SSL（SMTPS，端口通常为 465）。
            timeout: 连接超时（秒）。
            pool_size: 连接池大小。
            from_address: 默认发件人地址。
            from_name: 默认发件人显示名称。
        """
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_address = from_address
        self._from_name = from_name

        self._pool = ConnectionPool(
            host=host,
            port=port,
            use_tls=use_tls,
            use_ssl=use_ssl,
            timeout=timeout,
            max_connections=pool_size,
        )

    def send(
        self,
        to: str | list[str],
        subject: str,
        text: str = "",
        html: str = "",
        from_address: str = "",
        from_name: str = "",
        cc: str | list[str] = "",
        bcc: str | list[str] = "",
        reply_to: str = "",
        attachments: list[str | Path] | None = None,
    ) -> None:
        """发送邮件。

        Args:
            to: 收件人地址（单个或列表）。
            subject: 邮件主题。
            text: 纯文本内容。
            html: HTML 内容。
            from_address: 发件人地址（覆盖默认值）。
            from_name: 发件人显示名称（覆盖默认值）。
            cc: 抄送人地址。
            bcc: 密送人地址。
            reply_to: 回复地址。
            attachments: 附件文件路径列表。
        """
        msg = Message()

        # 发件人
        sender = from_address or self._from_address
        sender_name = from_name or self._from_name
        if sender:
            msg.from_(sender, sender_name)

        # 收件人
        if isinstance(to, str):
            msg.to(to)
        else:
            msg.to(*to)

        if cc:
            if isinstance(cc, str):
                msg.cc(cc)
            else:
                msg.cc(*cc)

        if bcc:
            if isinstance(bcc, str):
                msg.bcc(bcc)
            else:
                msg.bcc(*bcc)

        if reply_to:
            msg.reply_to(reply_to)

        # 内容
        msg.subject(subject)
        if text:
            msg.text(text)
        if html:
            msg.html(html)

        # 附件
        if attachments:
            for path in attachments:
                msg.attach(path)

        self.send_message(msg)

    def send_message(self, message: Message) -> None:
        """发送 Message 对象。

        Args:
            message: Message 实例。

        Raises:
            AuthenticationError: 认证失败。
            SMTPError: SMTP 错误。
            MailError: 其他邮件错误。
        """
        if not message._from and self._from_address:
            message.from_(self._from_address, self._from_name)

        if not message._from:
            raise MailError("未设置发件人地址")

        if not message.recipients:
            raise MailError("未设置收件人地址")

        mime_msg = message.build()

        conn = self._pool.get()
        try:
            # 认证
            if self._username and self._password:
                try:
                    conn.login(self._username, self._password)
                except smtplib.SMTPAuthenticationError as e:
                    raise AuthenticationError(
                        f"SMTP 认证失败: {e}",
                        original=e,
                    ) from e

            # 发送
            try:
                conn.sendmail(
                    message._from.split("<")[-1].rstrip(">"),
                    message.recipients,
                    mime_msg.as_string(),
                )
                logger.info(
                    "邮件发送成功: from=%s, to=%s, subject=%s",
                    message._from,
                    message.recipients,
                    message._subject,
                )
            except smtplib.SMTPException as e:
                raise SMTPError(f"邮件发送失败: {e}", original=e) from e

        finally:
            self._pool.release(conn)

    def create_message(self) -> Message:
        """创建新的 Message 构建器。

        Returns:
            Message 实例。
        """
        msg = Message()
        if self._from_address:
            msg.from_(self._from_address, self._from_name)
        return msg

    def close(self) -> None:
        """关闭连接池，释放所有连接。"""
        self._pool.close_all()
        logger.info("邮件发送器已关闭")

    @property
    def pool(self) -> ConnectionPool:
        """底层连接池。"""
        return self._pool

    def __enter__(self) -> Mailer:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        return (
            f"Mailer(host={self._host!r}, port={self._port}, "
            f"from={self._from_address!r})"
        )
