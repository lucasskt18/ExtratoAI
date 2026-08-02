from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.statement import Statement


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    statement_id: Mapped[int] = mapped_column(ForeignKey("statements.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    installment: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id"), nullable=True
    )

    statement: Mapped[Statement] = relationship(back_populates="transactions")
    category: Mapped[Optional[Category]] = relationship(back_populates="transactions")
