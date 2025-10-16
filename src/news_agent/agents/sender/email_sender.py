import logging
from email.message import EmailMessage
from typing import Dict

import aiosmtplib
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from news_agent.agents.db.sqlachemy_db import (
    SQLAlchemySubscriptionDB,
    Subscription,
    Trend,
    trend_tags,
)
from news_agent.agents.sender.abstract import AbstractSender

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class EmailSenderAgent(AbstractSender):
    def __init__(
        self,
        db: SQLAlchemySubscriptionDB,
        smtp_user: str,
        smtp_pass: str,
    ):
        self.db = db
        self.smtp_user = smtp_user
        self.smtp_pass = smtp_pass
        self.configure()

    def configure(self, settings: dict | None = None) -> None:
        self.smtp_config = {
            "host": "smtp.gmail.com",
            "port": 587,
            "username": self.smtp_user,
            "password": self.smtp_pass,
            "from_address": self.smtp_user,
        }

    async def send(self, to_address: str, data: Dict) -> bool:
        """Send an email with one or more trends."""
        trends = data.get("trends", [])

        if not trends:
            logger.warning(f"No trends to send to {to_address}")
            return False

        message = EmailMessage()
        message["From"] = self.smtp_config["from_address"]
        message["To"] = to_address

        # Subject line shows count of trends
        if len(trends) == 1:
            message["Subject"] = f"New Trend: {trends[0]['topic']}"
        else:
            message["Subject"] = f"{len(trends)} New Trends for You"

        # Build email body with all trends
        email_body = []
        for i, trend in enumerate(trends, 1):
            email_body.append(f"{i}. {trend['topic']}")
            email_body.append(f"   {trend['summary']}")
            email_body.append(f"   Read more: {trend['url']}")
            email_body.append("")  # Empty line between trends

        message.set_content("\n".join(email_body))

        try:
            await aiosmtplib.send(
                message,
                hostname=self.smtp_config["host"],
                port=self.smtp_config["port"],
                start_tls=True,
                username=self.smtp_config["username"],
                password=self.smtp_config["password"],
                timeout=30,
            )
            logger.info(f"✅ Email sent to {to_address} with {len(trends)} trend(s)")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_address}: {e}")
            return False

    async def send_for_subscriptions(self) -> dict:
        """Send trends to all subscribers based on their tags."""
        sent_count = 0
        failed_count = 0

        async with self.db.get_db() as db:
            # Load all subscriptions with tags
            result = await db.execute(
                select(Subscription).options(selectinload(Subscription.tags))
            )
            subscriptions = result.scalars().all()  # Fixed: removed [-1]

            for subscription in subscriptions:
                email = subscription.email

                # Get tag IDs for this subscription
                tag_ids = [tag.id for tag in subscription.tags]

                if not tag_ids:
                    continue

                # Get all unnotified trends matching subscriber's tags
                trends_result = await db.execute(
                    select(Trend)
                    .join(trend_tags, Trend.id == trend_tags.c.trend_id)
                    .where(trend_tags.c.tag_id.in_(tag_ids))
                    .where(Trend.notified.is_(False))
                    .distinct()  # Avoid duplicates if trend has multiple matching tags
                )
                trends = trends_result.scalars().all()

                if not trends:
                    logger.info(f"No new trends for {email}")
                    continue

                # Send all trends in one email per subscriber
                trends_payload = [
                    {"topic": t.topic, "summary": t.summary, "url": t.url}
                    for t in trends
                ]
                try:
                    if await self.send(email, {"trends": trends_payload}):
                        for t in trends:
                            t.notified = True
                        sent_count += len(trends)
                        await db.commit()  # Commit per successful send
                except Exception as e:
                    failed_count += len(trends)
                    logger.error(f"Error sending trends to {email}: {e}")
                    await db.rollback()  # Rollback on failure

        return {
            "sent_count": sent_count,
            "failed_count": failed_count,
            "total_subscriptions": len(subscriptions),
        }
