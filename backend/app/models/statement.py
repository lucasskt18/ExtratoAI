from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.transaction import Transaction


class Statement(Base):
    __tablename__ = "statements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bank: Mapped[str] = mapped_column(String(80), nullable=False)
    card_label: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    period_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    period_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="processed")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    transactions: Mapped[list[Transaction]] = relationship(
        back_populates="statement", cascade="all, delete-orphan"
    )
