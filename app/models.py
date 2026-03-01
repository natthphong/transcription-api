from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, Integer, BigInteger, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

class Base(DeclarativeBase):
    pass

class YoutubeTransaction(Base):
    __tablename__ = "tbl_youtube_transaction"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    youtube_link: Mapped[str] = mapped_column(Text, nullable=False)
    user_id_token: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # optional recommended fields (if you add columns)
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_auto_caption: Mapped[bool | None] = mapped_column(nullable=True)
    split_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tolerance_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    details = relationship("YoutubeTransactionDetail", back_populates="transaction")

class YoutubeTransactionDetail(Base):
    __tablename__ = "tbl_youtube_transaction_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    youtube_transaction_id: Mapped[int] = mapped_column(ForeignKey("tbl_youtube_transaction.id"))
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Your original fields (not ideal for offset but keep)
    start_timestamp: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_timestamp: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # recommended fields
    seq: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    end_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    clip_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    transaction = relationship("YoutubeTransaction", back_populates="details")