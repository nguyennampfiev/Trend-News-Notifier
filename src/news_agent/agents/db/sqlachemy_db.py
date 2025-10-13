import asyncio
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
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

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
# INITIALIZATION
# =====================================================


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)


# =====================================================
# DATABASE CLASS
# =====================================================


class SQLAlchemySubscriptionDB:
    """Async DB layer for subscriptions, tags, and trends."""

    def __init__(self):
        asyncio.create_task(init_db())  # initialize schema at startup

    # -----------------------
    # Subscription methods
    # -----------------------
    async def add_subscription(self, subscription: Subscription):
        async with get_db() as db:
            db.add(subscription)
            await db.commit()
            await db.refresh(subscription)
            return subscription

    async def get_subscriptions(self) -> List[Subscription]:
        async with get_db() as db:
            result = await db.execute(select(Subscription))
            return result.scalars().all()

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
    async def add_trend(self, trend: Trend):
        async with get_db() as db:
            db.add(trend)
            await db.commit()
            await db.refresh(trend)
            return trend

    async def get_all_topics(self, limit: int = 10) -> List[str]:
        async with get_db() as db:
            result = await db.execute(
                select(Trend.topic).order_by(Trend.id.desc()).limit(limit)
            )
            return [row[0] for row in result.all()]

    async def select_trend_by_topic_or_link(self, topic: str, link: str):
        async with get_db() as db:
            result = await db.execute(
                select(Trend)
                .where(
                    (func.lower(Trend.topic) == func.lower(topic))
                    | (func.lower(Trend.url) == func.lower(link))
                )
                .limit(1)
            )
            return result.scalars().first()
