"""
lmail 异常定义。
"""


class MailError(Exception):
    """邮件操作异常基类。"""

    def __init__(self, message: str = "", original: Exception | None = None) -> None:
        self.original = original
        super().__init__(message)


class SMTPError(MailError):
    """SMTP 协议错误。"""


class ConnectionError(MailError):
    """连接失败异常。"""


class AuthenticationError(MailError):
    """认证失败异常。"""
