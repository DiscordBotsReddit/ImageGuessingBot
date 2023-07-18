from sqlalchemy import BigInteger, Identity, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Points(Base):
    __tablename__ = "points"
    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    guild_id: Mapped[int] = mapped_column(BigInteger)
    user_id: Mapped[int] = mapped_column(BigInteger)
    points: Mapped[int] = mapped_column(Integer)
