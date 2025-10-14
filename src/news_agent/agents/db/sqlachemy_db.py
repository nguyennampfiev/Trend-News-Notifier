import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, relationship, selectinload, sessionmaker

logger = logging.getLogger("subscription_db")
logging.basicConfig(level=logging.INFO)

# =====================================================
# CONFIGURATION
# =====================================================

DATABASE_URL = "sqlite+aiosqlite:///./subscriptions.db"
Base = declarative_base()

# =====================================================
# ASSOCIATION TABLES
# =====================================================

subscription_tags = Table(
    "subscription_tags",
    Base.metadata,
    Column(
        "subscription_id", Integer, ForeignKey("subscriptions.id"), primary_key=True
    ),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)

trend_tags = Table(
    "trend_tags",
    Base.metadata,
    Column("trend_id", Integer, ForeignKey("trends.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)

# =====================================================
# MODELS
# =====================================================


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(256), nullable=False, unique=True)
    notes = Column(Text, nullable=True)
    tags = relationship(
        "Tag", secondary=subscription_tags, back_populates="subscriptions"
    )


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False)
    subscriptions = relationship(
        "Subscription", secondary=subscription_tags, back_populates="tags"
    )
    trends = relationship("Trend", secondary=trend_tags, back_populates="tags")


class Trend(Base):
    __tablename__ = "trends"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String(512), nullable=False)
    summary = Column(Text, nullable=True)
    url = Column(String(2048), nullable=True)
    source = Column(String(256), nullable=True)
    notified = Column(Boolean, default=False)
    tags = relationship("Tag", secondary=trend_tags, back_populates="trends")


# =====================================================
# ENGINE & SESSION
# =====================================================

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# =====================================================
# ASYNC CONTEXT MANAGER
# =====================================================


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# =====================================================
# DATABASE CLASS
# =====================================================


class SQLAlchemySubscriptionDB:
    """Async DB layer for subscriptions, tags, and trends."""

    async def init_db(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)

    # -----------------------
    # Subscription methods
    # -----------------------
    async def add_subscription(
        self, email: str, topics: list[str], notes: str | None = None
    ):
        async with get_db() as db:
            logger.info(
                "💾 add_subscription called with email=%s, topics=%s", email, topics
            )

            result = await db.execute(
                select(Subscription)
                .where(Subscription.email == email)
                .options(selectinload(Subscription.tags))
            )
            subscription = result.scalar_one_or_none()

            if subscription:
                if notes:
                    subscription.notes = notes
            else:
                subscription = Subscription(email=email, notes=notes)
                db.add(subscription)
                await db.flush()
                await db.refresh(subscription, ["tags"])

            for topic in topics:
                tag_result = await db.execute(select(Tag).where(Tag.name == topic))
                tag = tag_result.scalar_one_or_none()
                if not tag:
                    tag = Tag(name=topic)
                    db.add(tag)
                    await db.flush()
                if tag not in subscription.tags:
                    subscription.tags.append(tag)

            await db.commit()
            await db.refresh(subscription, ["tags"])
            return {
                "id": subscription.id,
                "email": subscription.email,
                "tags": [t.name for t in subscription.tags],
            }

    # -----------------------
    # Tag methods
    # -----------------------
    async def add_tag(self, tag: Tag):
        async with get_db() as db:
            db.add(tag)
            await db.commit()
            await db.refresh(tag)
            return tag

    # -----------------------
    # Trend methods
    # -----------------------
    async def add_trend(self, topic: str, summary: str, url: str, tag: str):
        async with get_db() as db:
            trend = Trend(topic=topic, summary=summary, url=url, notified=False)
            db.add(trend)
            await db.flush()

            results = await db.execute(select(Tag).where(Tag.name == tag))
            tag_obj = results.scalar_one_or_none()
            if not tag_obj:
                tag_obj = Tag(name=tag)
                db.add(tag_obj)
                await db.flush()

            if tag_obj not in trend.tags:
                trend.tags.append(tag_obj)

            await db.commit()
            logger.info(f"✅ Trend saved with tags: {tag}")

    async def get_all_topics(self, limit: int = 10) -> List[str]:
        async with get_db() as db:
            result = await db.execute(
                select(Tag.name).order_by(Tag.id.desc()).limit(limit)
            )
            return [row[0] for row in result.all()]

    # ✅ FIX: no async context here — this just builds a query for reuse
    def select_trend_by_topic_or_link(self, topic: str, link: str):
        return (
            select(Trend)
            .where(
                (func.lower(Trend.topic) == func.lower(topic))
                | (func.lower(Trend.url) == func.lower(link))
            )
            .limit(1)
        )

    # ✅ FIXED: single async context — this is now safe
    async def db_exists(self, topic: str, link: str) -> bool:
        async with get_db() as db:
            try:
                result = await db.execute(
                    self.select_trend_by_topic_or_link(topic, link)
                )
                exists = result.scalar_one_or_none() is not None
                return exists
            except Exception as e:
                logger.error(f"Database existence check failed: {e}")
                return False

    async def get_trends_for_user(self, email: str) -> list[Trend]:
        async with get_db() as db:
            result = await db.execute(
                select(Subscription)
                .where(Subscription.email == email)
                .options(selectinload(Subscription.tags))
            )
            subscription = result.scalar_one_or_none()
            if not subscription:
                return []

            tag_ids = [t.id for t in subscription.tags]
            if not tag_ids:
                logger.info(f"User {email} has no tags — skipping.")
                return []

            trend_result = await db.execute(
                select(Trend)
                .join(Trend.tags)
                .where(Tag.id.in_(tag_ids))
                .where(Trend.notified.is_(False))
                .options(selectinload(Trend.tags))
            )
            trends = trend_result.scalars().unique().all()
            return trends
