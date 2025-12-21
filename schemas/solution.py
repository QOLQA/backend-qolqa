from sqlalchemy import Integer, String, Text, ForeignKey, ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

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
    submodels: Mapped[str] = mapped_column(Text)

    queries: Mapped[list[Query]] = relationship("Query", cascade='all, delete')
