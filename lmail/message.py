"""
邮件消息构建器。

提供链式 API 构建 MIME 邮件，支持 HTML、纯文本、附件。
"""

from __future__ import annotations

import mimetypes
import os
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any


class Message:
    """邮件消息构建器。

    支持链式调用构建邮件。

    典型用法：
        msg = (
            Message()
            .from_("sender@example.com")
            .to("recipient@example.com")
            .subject("测试邮件")
            .html("<h1>你好!</h1>")
            .attach("file.pdf")
        )
    """

    def __init__(self) -> None:
        """初始化消息构建器。"""
        self._from: str = ""
        self._to: list[str] = []
        self._cc: list[str] = []
        self._bcc: list[str] = []
        self._reply_to: str = ""
        self._subject: str = ""
        self._text: str = ""
        self._html: str = ""
        self._attachments: list[tuple[str, bytes, str]] = []  # (filename, data, mimetype)
        self._headers: dict[str, str] = {}

    def from_(self, address: str, name: str = "") -> Message:
        """设置发件人。

        Args:
            address: 发件人邮箱地址。
            name: 发件人显示名称。

        Returns:
            self，便于链式调用。
        """
        if name:
            self._from = f"{name} <{address}>"
        else:
            self._from = address
        return self

    def to(self, *addresses: str) -> Message:
        """设置收件人。

        Args:
            *addresses: 一个或多个收件人邮箱地址。

        Returns:
            self，便于链式调用。
        """
        self._to.extend(addresses)
        return self

    def cc(self, *addresses: str) -> Message:
        """设置抄送人。

        Args:
            *addresses: 一个或多个抄送人邮箱地址。

        Returns:
            self，便于链式调用。
        """
        self._cc.extend(addresses)
        return self

    def bcc(self, *addresses: str) -> Message:
        """设置密送人。

        Args:
            *addresses: 一个或多个密送人邮箱地址。

        Returns:
            self，便于链式调用。
        """
        self._bcc.extend(addresses)
        return self

    def reply_to(self, address: str) -> Message:
        """设置回复地址。

        Args:
            address: 回复邮箱地址。

        Returns:
            self，便于链式调用。
        """
        self._reply_to = address
        return self

    def subject(self, subject: str) -> Message:
        """设置邮件主题。

        Args:
            subject: 邮件主题。

        Returns:
            self，便于链式调用。
        """
        self._subject = subject
        return self

    def text(self, content: str) -> Message:
        """设置纯文本内容。

        Args:
            content: 纯文本内容。

        Returns:
            self，便于链式调用。
        """
        self._text = content
        return self

    def html(self, content: str) -> Message:
        """设置 HTML 内容。

        Args:
            content: HTML 内容。

        Returns:
            self，便于链式调用。
        """
        self._html = content
        return self

    def attach(
        self,
        path: str | Path,
        filename: str | None = None,
        mimetype: str | None = None,
    ) -> Message:
        """添加附件。

        Args:
            path: 附件文件路径。
            filename: 附件显示名称，默认使用文件名。
            mimetype: MIME 类型，默认自动检测。

        Returns:
            self，便于链式调用。
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"附件文件不存在: {path}")

        data = path.read_bytes()
        display_name = filename or path.name

        if mimetype is None:
            mimetype, _ = mimetypes.guess_type(str(path))
            mimetype = mimetype or "application/octet-stream"

        self._attachments.append((display_name, data, mimetype))
        return self

    def attach_data(
        self,
        filename: str,
        data: bytes,
        mimetype: str = "application/octet-stream",
    ) -> Message:
        """添加二进制附件。

        Args:
            filename: 附件显示名称。
            data: 附件二进制数据。
            mimetype: MIME 类型。

        Returns:
            self，便于链式调用。
        """
        self._attachments.append((filename, data, mimetype))
        return self

    def header(self, name: str, value: str) -> Message:
        """添加自定义邮件头。

        Args:
            name: 邮件头名称。
            value: 邮件头值。

        Returns:
            self，便于链式调用。
        """
        self._headers[name] = value
        return self

    def build(self) -> MIMEMultipart | MIMEText:
        """构建 MIME 邮件对象。

        Returns:
            MIMEMultipart 或 MIMEText 对象。
        """
        if self._attachments or (self._text and self._html):
            msg = MIMEMultipart("mixed" if self._attachments else "alternative")
        else:
            subtype = "html" if self._html else "plain"
            content = self._html or self._text
            msg = MIMEText(content, subtype, "utf-8")

        # 设置基本头
        if self._from:
            msg["From"] = self._from
        if self._to:
            msg["To"] = ", ".join(self._to)
        if self._cc:
            msg["Cc"] = ", ".join(self._cc)
        if self._reply_to:
            msg["Reply-To"] = self._reply_to
        if self._subject:
            msg["Subject"] = Header(self._subject, "utf-8").encode()

        # 自定义头
        for name, value in self._headers.items():
            msg[name] = value

        # 添加内容部分
        if self._text and self._html:
            alt_part = MIMEMultipart("alternative")
            alt_part.attach(MIMEText(self._text, "plain", "utf-8"))
            alt_part.attach(MIMEText(self._html, "html", "utf-8"))
            msg.attach(alt_part)
        elif self._text:
            if isinstance(msg, MIMEMultipart):
                msg.attach(MIMEText(self._text, "plain", "utf-8"))
        elif self._html:
            if isinstance(msg, MIMEMultipart):
                msg.attach(MIMEText(self._html, "html", "utf-8"))

        # 添加附件
        for filename, data, mimetype in self._attachments:
            maintype, subtype = mimetype.split("/", 1)
            attachment = MIMEApplication(data, _subtype=subtype)
            attachment.add_header(
                "Content-Disposition",
                "attachment",
                filename=("utf-8", "", filename),
            )
            msg.attach(attachment)

        return msg

    @property
    def recipients(self) -> list[str]:
        """获取所有收件人地址（to + cc + bcc）。"""
        return self._to + self._cc + self._bcc

    def __repr__(self) -> str:
        return (
            f"Message(from={self._from!r}, to={self._to}, "
            f"subject={self._subject!r})"
        )
