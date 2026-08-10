"""
lmail — 轻量级邮件发送库。

特性：
    - 简洁的链式 API
    - 支持 HTML/纯文本/附件
    - 连接池复用
    - 零外部依赖（仅用标准库）

典型用法：
    from lmail import Mailer

    mailer = Mailer(host="smtp.example.com", port=587, use_tls=True)

    mailer.send(
        to="user@example.com",
        subject="欢迎",
        html="<h1>你好!</h1>",
    )
"""

from lmail.mailer import Mailer
from lmail.message import Message
from lmail.connection import ConnectionPool
from lmail.exceptions import (
    MailError,
    SMTPError,
    ConnectionError,
    AuthenticationError,
)

__version__ = "0.1.0"

__all__ = [
    "Mailer",
    "Message",
    "ConnectionPool",
    "MailError",
    "SMTPError",
    "ConnectionError",
    "AuthenticationError",
]
