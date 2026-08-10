# lmail

轻量级邮件发送库，支持 HTML/附件/连接池，零外部依赖。

## 特性

- **简洁 API**：一行代码发送邮件
- **链式构建**：Message 对象支持链式调用
- **连接池**：复用 SMTP 连接，减少握手开销
- **多格式**：支持纯文本、HTML、附件
- **零依赖**：仅使用 Python 标准库

## 安装

```bash
pip install lmail
```

## 快速开始

```python
from lmail import Mailer

# 创建发送器
mailer = Mailer(
    host="smtp.example.com",
    port=587,
    username="your_email@example.com",
    password="your_password",
    use_tls=True,
    from_address="your_email@example.com",
    from_name="Your Name",
)

# 发送邮件
mailer.send(
    to="recipient@example.com",
    subject="欢迎",
    html="<h1>你好!</h1><p>欢迎使用我们的服务。</p>",
)
```

## 高级用法

### 使用 Message 构建器

```python
from lmail import Mailer, Message

mailer = Mailer(host="smtp.example.com", port=587)

msg = (
    Message()
    .from_("sender@example.com", "发件人")
    .to("recipient@example.com")
    .cc("cc@example.com")
    .subject("测试邮件")
    .html("<h1>你好!</h1>")
    .attach("document.pdf")
    .attach_data("data.csv", b"col1,col2\n1,2", "text/csv")
)

mailer.send_message(msg)
```

### 上下文管理器

```python
with Mailer(host="smtp.example.com", port=587) as mailer:
    mailer.send(to="user@example.com", subject="测试", text="内容")
```

### 多收件人

```python
mailer.send(
    to=["user1@example.com", "user2@example.com"],
    cc=["cc@example.com"],
    bcc=["bcc@example.com"],
    subject="群发",
    html="<p>大家好!</p>",
)
```

## 配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `host` | `str` | - | SMTP 服务器地址 |
| `port` | `int` | `587` | SMTP 端口 |
| `username` | `str` | `""` | 登录用户名 |
| `password` | `str` | `""` | 登录密码 |
| `use_tls` | `bool` | `True` | 使用 STARTTLS |
| `use_ssl` | `bool` | `False` | 使用 SSL（SMTPS） |
| `timeout` | `float` | `30.0` | 连接超时（秒） |
| `pool_size` | `int` | `5` | 连接池大小 |
| `from_address` | `str` | `""` | 默认发件人地址 |
| `from_name` | `str` | `""` | 默认发件人名称 |

## 许可证

MIT
