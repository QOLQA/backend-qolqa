from sqlalchemy import Integer, String, Text, ForeignKey, ARRAY, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime

class Base(DeclarativeBase):
    pass


class Query(Base):
    __tablename__ = 'queries'

    _id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    solution_id: Mapped[int] = mapped_column(ForeignKey('solutions.id'), nullable=False)
    full_query: Mapped[str] = mapped_column(String(255), nullable=False)
    collections: Mapped[list[str]] = mapped_column(ARRAY(String))
    highlighted_words: Mapped[list[str]] = mapped_column(ARRAY(String))

    solution: Mapped["Solution"] = relationship("Solution", back_populates="queries")


class Solution(Base):
    __tablename__ = 'solutions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_version_saved: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    src_img: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    last_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    submodels: Mapped[str] = mapped_column(Text)

    queries: Mapped[list[Query]] = relationship("Query", cascade='all, delete')
