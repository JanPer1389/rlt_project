from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, Text, ForeignKey
from bot.dao.database import Base


class User(Base):
    __tablename__ = 'users'
    
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)  
    username: Mapped[str] = mapped_column(Text, nullable=False)
    first_name: Mapped[str] = mapped_column(Text, nullable=False)
    
    def __repr__(self):
        return f'Added User with name: <{self.first_name}>; username <{self.username}>'


class Videos(Base):
    __tablename__ = 'videos'
    
    id: Mapped[str] = mapped_column(Text, primary_key=True, autoincrement=False) 
    creator_id: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    video_created_at: Mapped[str] = mapped_column(Text)
    views_count: Mapped[str] = mapped_column(Text)
    likes_count: Mapped[str] = mapped_column(Text)
    comments_count: Mapped[str] = mapped_column(Text)
    reports_count: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)
    video_snap: Mapped['Video_Snapshots'] = relationship(
        'Video_Snapshots',
        back_populates='video',
        uselist=False,
        cascade='all, delete-orphan'
    )


class Video_Snapshots(Base):
    __tablename__ = 'video_snapshots'
    
    id: Mapped[str] = mapped_column(Text, primary_key=True, autoincrement=False)  
    video_id: Mapped[str] = mapped_column(ForeignKey('videos.id'), nullable=False)
    views_count: Mapped[str] = mapped_column(Text)
    likes_count: Mapped[str] = mapped_column(Text)
    comments_count: Mapped[str] = mapped_column(Text)
    reports_count: Mapped[str] = mapped_column(Text)
    delta_views_count: Mapped[str] = mapped_column(Text)
    delta_likes_count: Mapped[str] = mapped_column(Text)
    delta_comments_count: Mapped[str] = mapped_column(Text)
    delta_reports_count: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)
    video: Mapped['Videos'] = relationship('Videos', back_populates='video_snap')