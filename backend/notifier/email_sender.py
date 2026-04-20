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


def _clean_html(text):
    """Remove HTML tags from text for email safety"""
    if not text:
        return ""
    import re
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&amp;', '&').replace('&quot;', '"')
    return text.strip()


# Platform branding: color, display name
_PLATFORM_META = {
    "github":     ("#24292e", "GitHub"),
    "zhihu":      ("#0084ff", "知乎"),
    "bilibili":   ("#fb7299", "Bilibili"),
    "twitter":    ("#1da1f2", "X / Twitter"),
    "anthropic":  ("#d97757", "Anthropic"),
    "builderio":  ("#a855f7", "Builder.io"),
    "hackernews": ("#ff6600", "Hacker News"),
    "rss":        ("#10b981", "RSS"),
}


def build_email_html(summaries):
    """Build a polished dark-themed HTML email digest."""
    date_str = datetime.now().strftime('%Y-%m-%d')
    total = len(summaries)

    # Count per platform
    platform_counts = {}
    for summary, raw_content in summaries:
        platform_counts[raw_content.platform] = platform_counts.get(raw_content.platform, 0) + 1

    # Platform stat pills
    stat_pills = ""
    for platform, count in sorted(platform_counts.items(), key=lambda x: -x[1]):
        color, label = _PLATFORM_META.get(platform, ("#666666", platform.upper()))
        stat_pills += (
            f'<span style="display:inline-block;padding:4px 10px;border-radius:4px;'
            f'font-size:12px;background:{color}22;color:{color};border:1px solid {color}44;'
            f'margin:0 4px 4px 0;font-family:monospace;">'
            f'{label} {count}</span>'
        )

    # Summary cards
    cards_html = ""
    for summary, raw_content in summaries:
        color, label = _PLATFORM_META.get(raw_content.platform, ("#666666", raw_content.platform.upper()))
        title = _clean_html(raw_content.title) or "无标题"
        summary_text = _clean_html(summary.summary_text) or ""
        highlight = _clean_html(summary.highlight_sentence) if summary.highlight_sentence else None
        key_points = summary.key_points or []
        tags = summary.tags or []

        # Highlight block
        highlight_block = ""
        if highlight:
            highlight_block = (
                f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
                f'style="margin:12px 0;background:#f59e0a0a;border:1px solid #f59e0a33;border-radius:6px;">'
                f'<tr><td style="padding:10px 12px;">'
                f'<p style="margin:0;font-size:13px;color:#d4d4d4;line-height:1.6;font-style:italic;">'
                f'<span style="color:#f59e0a;margin-right:6px;">&#9733;</span>"{highlight}"'
                f'</p></td></tr></table>'
            )

        # Key points
        key_points_block = ""
        if key_points:
            kp_items = ""
            for i, point in enumerate(key_points[:4], 1):
                clean_point = _clean_html(point)
                kp_items += (
                    f'<tr><td style="padding:3px 0;vertical-align:top;" width="22">'
                    f'<span style="display:inline-block;width:18px;height:18px;line-height:18px;'
                    f'text-align:center;border-radius:4px;background:#00d4ff11;color:#00d4ff;'
                    f'font-size:11px;font-family:monospace;">{i}</span></td>'
                    f'<td style="padding:3px 0;font-size:13px;color:#c0c0c0;line-height:1.5;">'
                    f'{clean_point}</td></tr>'
                )
            key_points_block = (
                f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
                f'style="margin:10px 0;">{kp_items}</table>'
            )

        # Tags
        tags_block = ""
        if tags:
            tag_items = ""
            for tag in tags[:5]:
                tag_items += (
                    f'<span style="display:inline-block;padding:2px 8px;border-radius:3px;'
                    f'font-size:11px;background:#2a2a2a;color:#888888;border:1px solid #333333;'
                    f'margin:0 4px 4px 0;font-family:monospace;">{tag}</span>'
                )
            tags_block = f'<div style="margin-top:10px;">{tag_items}</div>'

        # Card HTML
        cards_html += (
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
            f'style="margin:0 0 14px 0;background:#141414;border:1px solid #222222;border-radius:10px;"">'
            f'<tr><td style="padding:16px;">'
            # Header: platform badge + title
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'<tr><td>'
            f'<span style="display:inline-block;padding:3px 8px;border-radius:4px;font-size:11px;'
            f'background:{color}22;color:{color};border:1px solid {color}44;font-family:monospace;'
            f'text-transform:uppercase;">{label}</span>'
            f'</td></tr>'
            f'<tr><td style="padding-top:10px;">'
            f'<h3 style="margin:0;font-size:16px;color:#e8e8e8;line-height:1.4;font-weight:600;">{title}</h3>'
            f'</td></tr></table>'
            # Summary text
            f'<p style="margin:10px 0 0 0;font-size:14px;color:#a0a0a0;line-height:1.6;">'
            f'{summary_text[:220]}{"..." if len(summary_text) > 220 else ""}</p>'
            # Highlight
            f'{highlight_block}'
            # Key points
            f'{key_points_block}'
            # Tags
            f'{tags_block}'
            # Footer: AI provider + link
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:12px;">'
            f'<tr><td style="font-size:11px;color:#555555;font-family:monospace;">'
            f'{summary.ai_provider or "AI"} &middot; {summary.ai_model or ""}'
            f'</td><td align="right">'
            f'<a href="{raw_content.url}" style="display:inline-block;padding:6px 14px;'
            f'background:#00d4ff11;color:#00d4ff;border:1px solid #00d4ff33;border-radius:5px;'
            f'font-size:12px;text-decoration:none;font-family:monospace;">查看原文 &rarr;</a>'
            f'</td></tr></table>'
            f'</td></tr></table>'
        )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>今日 AI 知识摘要 - {date_str}</title>
</head>
<body style="margin:0;padding:0;background:#0a0a0a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#0a0a0a;">
<tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;width:100%;">

<!-- Header -->
<tr><td style="background:#111111;border:1px solid #222222;border-radius:12px;padding:28px 24px;text-align:center;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
<tr><td style="text-align:center;">
<p style="margin:0 0 6px 0;font-size:12px;color:#00d4ff;font-family:monospace;letter-spacing:2px;">AI KNOWLEDGE HUB</p>
<h1 style="margin:0;font-size:24px;color:#ffffff;font-weight:700;">今日知识摘要</h1>
<p style="margin:8px 0 0 0;font-size:13px;color:#888888;font-family:monospace;">{date_str} &middot; 共 {total} 条内容</p>
</td></tr>
<tr><td style="padding-top:16px;text-align:center;">
{stat_pills}
</td></tr>
</table>
</td></tr>

<!-- Spacer -->
<tr><td height="16"></td></tr>

<!-- Content cards -->
<tr><td>
{cards_html}
</td></tr>

<!-- Footer CTA -->
<tr><td style="background:#111111;border:1px solid #222222;border-radius:12px;padding:20px;text-align:center;">
<p style="margin:0 0 12px 0;font-size:13px;color:#888888;">在网页端查看完整内容、收藏文章、记录笔记</p>
<a href="http://localhost:5173" style="display:inline-block;padding:10px 24px;background:#00d4ff22;color:#00d4ff;border:1px solid #00d4ff44;border-radius:6px;font-size:13px;text-decoration:none;font-family:monospace;">打开知识库 &rarr;</a>
</td></tr>

<!-- Copyright -->
<tr><td style="padding:20px 0;text-align:center;">
<p style="margin:0;font-size:11px;color:#444444;font-family:monospace;">AI Knowledge Hub &middot; 每日自动推送</p>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""


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
