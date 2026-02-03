from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, Text, ForeignKey, Date, DateTime
from bot.dao.database import Base


class User(Base):
    __tablename__ = 'user'
    
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, autoincrement=True)
    username: Mapped[str] = mapped_column(Text, nullable=False)
    first_name: Mapped[str] = mapped_column(Text, nullable=False)
    
    def __repr__(self):
        return f'Added User with name: <{self.first_name}; username <{self.username}>'
    __tablename__ = "videos"


class Videos(Base):
    __tablename__ = 'videos'
    id: Mapped[str] = mapped_column(Text)
    creator_id: Mapped[str] = mapped_column(Text)
    video_created_at: Mapped[str] = mapped_column(BigInteger)
    views_count: Mapped[int] = mapped_column(BigInteger)
    likes_count: Mapped[int] = mapped_column(BigInteger)
    comments_count: Mapped[int] = mapped_column(BigInteger)
    reports_count: Mapped[int] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)
    video_snap: Mapped['Video_Snapshots'] = relationship(
        'Video_Snapshots',
        back_populates='video_snap',
        uselist=False,
        cascade='all, delete-orphan'
    )


class Video_Snapshots(Base):
    __tablename__ = 'video_snap'
    
    id: Mapped[Optional[str]] = mapped_column(Text)
    video_id:Mapped[Optional[str]] = mapped_column(Text)
    views_count: Mapped[Optional[int]] = mapped_column(BigInteger)
    likes_count:Mapped[Optional[int]] = mapped_column(BigInteger)
    reports_count:Mapped[Optional[int]] = mapped_column(BigInteger)
    comments_count:Mapped[Optional[int]] = mapped_column(BigInteger)
    delta_views_count: Mapped[Optional[int]] = mapped_column(BigInteger)
    delta_likes_count: Mapped[Optional[int]] = mapped_column(BigInteger)
    delta_comments_count: Mapped[Optional[int]] = mapped_column(BigInteger)
    delta_reports_count:Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[Optional[str]] = mapped_column(Text)
    videos: Mapped['Videos'] = relationship('Videos', back_populates='videos', uselist=False, cascade='all, delete-orhan')