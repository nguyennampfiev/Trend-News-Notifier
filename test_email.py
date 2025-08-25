import asyncio
import os
from email.message import EmailMessage

import aiosmtplib
from dotenv import load_dotenv

load_dotenv()

SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
TO_EMAIL = os.getenv("RECIPIENT_EMAIL")


async def test_email():
    message = EmailMessage()
    message["From"] = SMTP_USER
    message["To"] = TO_EMAIL
    message["Subject"] = "Test Email"
    message.set_content("Test message")

    try:
        await aiosmtplib.send(
            message,
            hostname="smtp.gmail.com",
            port=587,
            username=SMTP_USER,
            password=SMTP_PASS,
            start_tls=True,
        )
        print("✅ Email sent")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_email())
