import logging
from email.message import EmailMessage
from typing import Dict

import aiosmtplib
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from news_agent.agents.db.sqlachemy_db import (
    SQLAlchemySubscriptionDB,
    Subscription,
    get_db,
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

    async def send(self, to_address: str, trend: Dict) -> bool:
        message = EmailMessage()
        message["From"] = self.smtp_config["from_address"]
        message["To"] = to_address
        message["Subject"] = f"New Trend: {trend['topic']}"
        message.set_content(f"{trend['summary']}\n\nRead more: {trend['url']}")

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
            logger.info(f"✅ Email sent to {to_address}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_address}: {e}")
            return False

    async def send_for_subscriptions(self) -> dict:
        """Send trends to all subscribers based on their tags."""
        sent_count = 0
        failed_count = 0

        async with get_db() as db:
            # Load all subscriptions from the database
            result = await db.execute(
                select(Subscription).options(selectinload(Subscription.tags))
            )
            subscriptions = result.scalars().all()

            for subscription in subscriptions:
                email = subscription.email
                trends = await self.db.get_trends_for_user(email)
                if not trends:
                    logger.info(f"No new trends for {email}")
                    continue

                for trend in trends:
                    try:
                        if await self.send(
                            email,
                            {
                                "topic": trend.topic,
                                "summary": trend.summary,
                                "url": trend.url,
                            },
                        ):
                            trend.notified = True
                            sent_count += 1
                    except Exception as e:
                        failed_count += 1
                        logger.error(
                            f"Error sending trend '{trend.topic}' to {email}: {e}"
                        )

            # Commit all changes (mark trends as notified)
            await db.commit()

        return {
            "sent_count": sent_count,
            "failed_count": failed_count,
            "total_subscriptions": len(subscriptions),
        }
