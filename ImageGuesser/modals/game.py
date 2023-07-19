from sqlalchemy import BigInteger, Identity, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Game(Base):
    __tablename__ = "games"
    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    guild_id: Mapped[int] = mapped_column(BigInteger)
    channel_id: Mapped[int] = mapped_column(BigInteger)
    timeout: Mapped[int] = mapped_column(Integer)
    quiz_bank: Mapped[int] = mapped_column(Integer)
