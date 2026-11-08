from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('member', 'admin')", name="ck_users_role"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(nullable=False, server_default="member")
    photo_path: Mapped[str | None] = mapped_column(default=None)
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default="1")
    failed_login_count: Mapped[int] = mapped_column(nullable=False, server_default="0")
    locked_until: Mapped[datetime | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())

    gifts_as_recipient: Mapped[list["Gift"]] = relationship(
        foreign_keys="Gift.recipient_id", back_populates="recipient"
    )
    gifts_as_author: Mapped[list["Gift"]] = relationship(
        foreign_keys="Gift.author_id", back_populates="author"
    )
    gifts_purchased: Mapped[list["Gift"]] = relationship(
        foreign_keys="Gift.purchased_by_id", back_populates="purchased_by"
    )
    reservations: Mapped[list["Reservation"]] = relationship(back_populates="user")
    comments: Mapped[list["Comment"]] = relationship(back_populates="author")


class Gift(Base):
    __tablename__ = "gifts"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_gifts_name_not_blank"),
        CheckConstraint("price IS NULL OR price >= 0", name="ck_gifts_price_positive"),
        CheckConstraint(
            "purchased_by_id IS NULL OR purchased_by_id <> recipient_id",
            name="ck_gifts_purchaser_not_recipient",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), default=None)
    url: Mapped[str | None] = mapped_column(default=None)
    image_path: Mapped[str | None] = mapped_column(default=None)
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    purchased_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None)
    purchased_at: Mapped[datetime | None] = mapped_column(default=None)
    removed_at: Mapped[datetime | None] = mapped_column(default=None)
    archived_year: Mapped[int | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())

    recipient: Mapped["User"] = relationship(
        foreign_keys=[recipient_id], back_populates="gifts_as_recipient"
    )
    author: Mapped["User"] = relationship(
        foreign_keys=[author_id], back_populates="gifts_as_author"
    )
    purchased_by: Mapped["User | None"] = relationship(
        foreign_keys=[purchased_by_id], back_populates="gifts_purchased"
    )
    reservations: Mapped[list["Reservation"]] = relationship(
        back_populates="gift", cascade="all, delete-orphan"
    )
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="gift", cascade="all, delete-orphan", order_by="Comment.created_at"
    )


Index("ix_gifts_recipient", Gift.recipient_id, sqlite_where=Gift.archived_year.is_(None))


class Reservation(Base):
    __tablename__ = "reservations"

    gift_id: Mapped[int] = mapped_column(
        ForeignKey("gifts.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())

    gift: Mapped["Gift"] = relationship(back_populates="reservations")
    user: Mapped["User"] = relationship(back_populates="reservations")


class Comment(Base):
    __tablename__ = "comments"
    __table_args__ = (
        CheckConstraint(
            "length(trim(content)) BETWEEN 1 AND 1000", name="ck_comments_content_length"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    gift_id: Mapped[int] = mapped_column(ForeignKey("gifts.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())
    updated_at: Mapped[datetime | None] = mapped_column(default=None)

    gift: Mapped["Gift"] = relationship(back_populates="comments")
    author: Mapped["User"] = relationship(back_populates="comments")


Index("ix_comments_gift", Comment.gift_id, Comment.created_at)
