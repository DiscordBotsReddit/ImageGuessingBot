from sqlalchemy import BigInteger, Identity, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Image(Base):
    __tablename__ = "images"
    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    guild_id: Mapped[int] = mapped_column(BigInteger)
    image_url: Mapped[str] = mapped_column(Text)
    solution: Mapped[str] = mapped_column(Text)
    quiz_bank: Mapped[str] = mapped_column(Text)
