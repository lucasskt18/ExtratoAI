from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.merchant_rule import MerchantRule
    from app.models.transaction import Transaction


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(20), nullable=False, default="#6B7280")
    keywords: Mapped[str] = mapped_column(Text, nullable=False, default="")

    transactions: Mapped[list[Transaction]] = relationship(back_populates="category")
    merchant_rules: Mapped[list[MerchantRule]] = relationship(back_populates="category")
