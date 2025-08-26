import logging
from email.message import EmailMessage
from typing import Dict, List

import aiosmtplib

from news_agent.agents.db.db import AbstractTrendDB
from news_agent.agents.sender.abstract import AbstractSender

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class EmailSenderAgent(AbstractSender):
    def __init__(
        self, db: AbstractTrendDB, smtp_user: str, smtp_pass: str, recipients: List[str]
    ):
        self.db = db
        self.smtp_user = smtp_user
        self.smtp_pass = smtp_pass
        # Clean recipients
        self.recipients = [r.strip("[]").strip() for r in recipients]
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
        message["To"] = to_address.strip("[]").strip()  # Clean address
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
                timeout=30,  # Add timeout
            )
            logger.info(f"✅ Email sent to {to_address}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_address}: {e}")
            return False

    async def send_unsent(self) -> dict:
        """Fetch unsent trends from DB and send them via email."""
        unsent = self.db.get_unsent_trends()
        logger.info(f"Unsent trends: {unsent}")
        sent_count = 0
        failed_count = 0

        for trend in unsent:
            logger.info(f"Processing trend: {trend['topic']}")
            trend_sent_successfully = False

            for recipient in self.recipients:
                logger.info(f"Sending to {recipient}")
                try:
                    if await self.send(recipient, trend):
                        sent_count += 1
                        trend_sent_successfully = True
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Error sending to {recipient}: {e}")
                    failed_count += 1

            # Only mark as sent if at least one recipient got it successfully
            if trend_sent_successfully:
                self.db.mark_as_sent(trend["id"])
                logger.info(f"✅ Trend {trend['id']} marked as sent")
            else:
                logger.warning(
                    f"❌ Failed to send trend {trend['id']} to any recipient"
                )

        return {
            "sent_count": sent_count,
            "failed_count": failed_count,
            "total_unsent": len(unsent),
        }
