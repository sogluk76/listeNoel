"""Modèles SQLAlchemy (cf. docs/03-modele-donnees.md)."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

ROLE_MEMBER = "member"
ROLE_ADMIN = "admin"

STATUS_AVAILABLE = "available"
STATUS_RESERVED = "reserved"
STATUS_BOUGHT = "bought"
STATUS_REMOVED = "removed"


def utcnow() -> datetime:
    """Date/heure UTC sans fuseau (format stocké en base)."""
    return datetime.now(UTC).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('member', 'admin')", name="ck_users_role"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(10), nullable=False, default=ROLE_MEMBER)
    photo_path: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime)
    # Thème d'affichage choisi dans le profil (RG-56). « auto » suit l'appareil.
    theme: Mapped[str] = mapped_column(
        String(20), nullable=False, default="auto", server_default="auto"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )

    @property
    def is_member(self) -> bool:
        return self.role == ROLE_MEMBER

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN

    def is_locked(self, now: datetime | None = None) -> bool:
        return self.locked_until is not None and self.locked_until > (now or utcnow())


class Gift(Base):
    __tablename__ = "gifts"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_gifts_name"),
        CheckConstraint("price IS NULL OR price >= 0", name="ck_gifts_price"),
        CheckConstraint(
            "purchased_by_id IS NULL OR purchased_by_id <> recipient_id", name="ck_gifts_buyer"
        ),
        Index("ix_gifts_recipient", "recipient_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    url: Mapped[str | None] = mapped_column(Text)
    image_path: Mapped[str | None] = mapped_column(Text)
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    purchased_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    purchased_at: Mapped[datetime | None] = mapped_column(DateTime)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime)
    archived_year: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )

    recipient: Mapped[User] = relationship(foreign_keys=[recipient_id])
    author: Mapped[User] = relationship(foreign_keys=[author_id])
    purchased_by: Mapped[User | None] = relationship(foreign_keys=[purchased_by_id])
    reservations: Mapped[list["Reservation"]] = relationship(
        back_populates="gift", cascade="all, delete-orphan", order_by="Reservation.created_at"
    )
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="gift", cascade="all, delete-orphan", order_by="Comment.created_at"
    )

    @property
    def is_suggestion(self) -> bool:
        return self.author_id != self.recipient_id

    @property
    def is_removed(self) -> bool:
        return self.removed_at is not None

    @property
    def is_bought(self) -> bool:
        return self.purchased_by_id is not None

    @property
    def is_archived(self) -> bool:
        return self.archived_year is not None

    @property
    def status(self) -> str:
        if self.is_removed:
            return STATUS_REMOVED
        if self.is_bought:
            return STATUS_BOUGHT
        if self.reservations:
            return STATUS_RESERVED
        return STATUS_AVAILABLE


class Reservation(Base):
    __tablename__ = "reservations"

    gift_id: Mapped[int] = mapped_column(
        ForeignKey("gifts.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)

    gift: Mapped[Gift] = relationship(back_populates="reservations")
    user: Mapped[User] = relationship()


class Comment(Base):
    __tablename__ = "comments"
    __table_args__ = (
        CheckConstraint("length(trim(content)) BETWEEN 1 AND 1000", name="ck_comments_content"),
        Index("ix_comments_gift", "gift_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gift_id: Mapped[int] = mapped_column(ForeignKey("gifts.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)

    gift: Mapped[Gift] = relationship(back_populates="comments")
    author: Mapped[User] = relationship()
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="comment", cascade="all, delete-orphan"
    )


class Notification(Base):
    """Mention « @Prénom » dans un commentaire, à signaler au membre mentionné (RG-42)."""

    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("user_id", "comment_id", name="uq_notifications_user_comment"),
        Index("ix_notifications_user", "user_id", "read_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    comment_id: Mapped[int] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    read_at: Mapped[datetime | None] = mapped_column(DateTime)

    user: Mapped[User] = relationship()
    comment: Mapped[Comment] = relationship(back_populates="notifications")


class Conversation(Base):
    """Conversation privée : à deux (une seule par paire) ou groupe nommé (RG-46)."""

    __tablename__ = "conversations"
    __table_args__ = (
        CheckConstraint(
            "(is_group = 1 AND name IS NOT NULL AND direct_key IS NULL)"
            " OR (is_group = 0 AND name IS NULL AND direct_key IS NOT NULL)",
            name="ck_conversations_kind",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    is_group: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    name: Mapped[str | None] = mapped_column(String(60))
    # « petit_id:grand_id » pour une conversation à deux : garantit l'unicité de la paire.
    direct_key: Mapped[str | None] = mapped_column(String(40), unique=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)

    creator: Mapped[User] = relationship()
    members: Mapped[list["ConversationMember"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationMember.joined_at, ConversationMember.user_id",
    )
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="Message.id"
    )


class ConversationMember(Base):
    """Participant d'une conversation, et jusqu'où il a lu (RG-50, RG-51)."""

    __tablename__ = "conversation_members"
    __table_args__ = (Index("ix_conversation_members_user", "user_id"),)

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    # Identifiant du dernier message lu. Les messages suivants écrits par d'autres sont non lus.
    last_read_message_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    conversation: Mapped[Conversation] = relationship(back_populates="members")
    user: Mapped[User] = relationship()


class Message(Base):
    """Message privé : du texte, une photo, ou les deux (RG-48)."""

    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint(
            "length(content) <= 1000 AND (length(trim(content)) > 0 OR image_path IS NOT NULL)",
            name="ck_messages_content",
        ),
        Index("ix_messages_conversation", "conversation_id", "id"),
        # Un identifiant n'est jamais réutilisé : « lu jusqu'au message n » reste fiable
        # même après la suppression du dernier message.
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    image_path: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    author: Mapped[User] = relationship()
