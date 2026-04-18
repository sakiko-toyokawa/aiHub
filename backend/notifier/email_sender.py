import logging
from datetime import datetime, timedelta
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.config import get_settings
from app.database import SessionLocal
from app.models import Summary, RawContent

logger = logging.getLogger(__name__)


def _get_mail_config(settings):
    """根据端口自动选择 TLS/SSL 配置"""
    # 465 端口通常使用 SSL；587 端口通常使用 STARTTLS
    use_ssl = settings.smtp_port == 465
    return ConnectionConfig(
        MAIL_USERNAME=settings.smtp_user,
        MAIL_PASSWORD=settings.smtp_password,
        MAIL_FROM=settings.smtp_user,
        MAIL_PORT=settings.smtp_port,
        MAIL_SERVER=settings.smtp_host,
        MAIL_STARTTLS=not use_ssl,
        MAIL_SSL_TLS=use_ssl,
        USE_CREDENTIALS=True,
    )


async def send_daily_digest(force: bool = False):
    """Send daily email digest of new summaries"""
    settings = get_settings()

    if not force and not settings.email_enabled:
        logger.info("Email disabled, skipping daily digest")
        return

    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("Email not configured, skipping daily digest")
        return

    # Get today's summaries
    db = SessionLocal()
    try:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        summaries = db.query(Summary, RawContent).join(RawContent).filter(
            Summary.created_at >= today
        ).order_by(Summary.created_at.desc()).limit(20).all()

        if not summaries:
            logger.info("No new summaries today, skipping email")
            return

        # Build email content
        html_content = build_email_html(summaries)

        conf = _get_mail_config(settings)

        message = MessageSchema(
            subject=f"今日 AI 知识摘要 - {datetime.now().strftime('%Y-%m-%d')}",
            recipients=[settings.email_to] if settings.email_to else [settings.smtp_user],
            body=html_content,
            subtype="html"
        )

        fm = FastMail(conf)
        await fm.send_message(message)
        logger.info(f"Daily digest sent to {settings.email_to or settings.smtp_user}")

    finally:
        db.close()


def build_email_html(summaries):
    """Build HTML email content"""
    date_str = datetime.now().strftime('%Y-%m-%d')
    total = len(summaries)

    cards_html = ""
    for summary, raw_content in summaries:
        platform_color = {
            "github": "#24292e",
            "zhihu": "#0084ff",
            "bilibili": "#fb7299",
            "twitter": "#1da1f2"
        }.get(raw_content.platform, "#666")

        cards_html += f"""
        <div style="border: 1px solid #e0e0e0; margin: 10px 0; padding: 15px; border-radius: 8px;">
            <span style="display: inline-block; padding: 4px 8px; border-radius: 4px;
                         font-size: 12px; background: {platform_color}; color: white;">
                {raw_content.platform.upper()}
            </span>
            <h3 style="margin: 10px 0;">{raw_content.title or '无标题'}</h3>
            <p style="color: #666;">{summary.summary_text[:200]}...</p>
            <a href="{raw_content.url}" style="color: #1d9bf0;">查看原文 →</a>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: -apple-system, sans-serif; color: #333; max-width: 600px; margin: 0 auto; }}
            .header {{ background: #1a1a1a; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>今日 AI 知识摘要</h2>
            <p>{date_str} | 共 {total} 条内容</p>
        </div>
        <div class="content">
            {cards_html}
            <p><a href="http://localhost:3000">查看全部内容 →</a></p>
        </div>
    </body>
    </html>
    """


async def send_test_email():
    """Send test email to verify configuration"""
    settings = get_settings()

    if not settings.smtp_user or not settings.smtp_password:
        raise ValueError("Email not configured. Please set SMTP_USER and SMTP_PASSWORD")

    conf = _get_mail_config(settings)

    recipient = settings.email_to if settings.email_to else settings.smtp_user

    message = MessageSchema(
        subject="AI Knowledge Hub - 测试邮件",
        recipients=[recipient],
        body=f"""
        <h2>AI Knowledge Hub 测试邮件</h2>
        <p>如果您收到这封邮件，说明邮件配置正确！</p>
        <p>配置信息：</p>
        <ul>
            <li>SMTP服务器: {settings.smtp_host}:{settings.smtp_port}</li>
            <li>发件人: {settings.smtp_user}</li>
            <li>收件人: {recipient}</li>
            <li>发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
        </ul>
        """,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)
    logger.info(f"Test email sent to {recipient}")
