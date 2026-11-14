"""Messages privés entre membres (RG-46 à RG-55).

C'est le SEUL endroit qui décide de qui lit une conversation. Toute lecture de
conversations, de messages ou de photos passe par ce module, qui vérifie que le
viewer est participant : une URL tapée à la main renvoie une erreur 404.

Les messages privés ne sont rattachés à aucun cadeau : la matrice RG-30 ne
s'applique pas ici. L'admin n'a accès à rien (RG-46).
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.errors import Forbidden, Invalid, NotFound
from app.models import Conversation, ConversationMember, Message, User, utcnow
from app.services import images
from app.services import users as users_service

CONTENT_MAX = 1000
NAME_MAX = 60
ONLINE_SECONDS = 120
PHOTO_DIR = "messages"


@dataclass
class GroupAvatar:
    """Faux « membre » pour afficher l'avatar d'un groupe avec la macro avatar()."""

    first_name: str
    photo_path: str | None = None


@dataclass
class Summary:
    """Une ligne de la liste des conversations, telle que le viewer a le droit de la voir."""

    conversation: Conversation
    title: str
    avatar: object  # User (conversation à deux) ou GroupAvatar
    preview: str
    unread: int
    activity: datetime


# --- Accès (RG-47) -----------------------------------------------------------


def membership(conversation: Conversation, user: User) -> ConversationMember | None:
    return next((m for m in conversation.members if m.user_id == user.id), None)


def get_conversation(db: Session, viewer: User, conversation_id: int) -> Conversation:
    """Conversation dont le viewer est participant, sinon 404 (y compris pour une URL forgée)."""
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or not viewer.is_member or membership(conversation, viewer) is None:
        raise NotFound()
    return conversation


def get_group(db: Session, viewer: User, conversation_id: int) -> Conversation:
    conversation = get_conversation(db, viewer, conversation_id)
    if not conversation.is_group:
        raise NotFound()
    return conversation


def get_message(db: Session, viewer: User, message_id: int) -> Message:
    """Message d'une conversation du viewer, sinon 404."""
    message = db.get(Message, message_id)
    if message is None:
        raise NotFound()
    get_conversation(db, viewer, message.conversation_id)
    return message


def get_own_message(db: Session, viewer: User, message_id: int) -> Message:
    """Message écrit par le viewer. 404 s'il ne peut pas le voir, 403 s'il n'est pas à lui."""
    message = get_message(db, viewer, message_id)
    if message.author_id != viewer.id:
        raise Forbidden()
    return message


def photo_file(db: Session, viewer: User, message_id: int) -> Path:
    """Fichier de la photo d'un message, réservé aux participants (RG-47)."""
    message = get_message(db, viewer, message_id)
    if not message.image_path:
        raise NotFound()
    root = settings.private_media_dir.resolve()
    target = (root / message.image_path).resolve()
    if root not in target.parents or not target.is_file():
        raise NotFound()
    return target


def _my_conversations(db: Session, viewer: User) -> list[Conversation]:
    stmt = (
        select(Conversation)
        .join(ConversationMember, ConversationMember.conversation_id == Conversation.id)
        .where(ConversationMember.user_id == viewer.id)
    )
    return list(db.scalars(stmt).all())


# --- Présentation ------------------------------------------------------------


def other(conversation: Conversation, viewer: User) -> User:
    """L'autre participant d'une conversation à deux."""
    return next(m.user for m in conversation.members if m.user_id != viewer.id)


def title(conversation: Conversation, viewer: User) -> str:
    return conversation.name if conversation.is_group else other(conversation, viewer).first_name


def avatar(conversation: Conversation, viewer: User):
    if conversation.is_group:
        return GroupAvatar(first_name=conversation.name)
    return other(conversation, viewer)


def can_write(conversation: Conversation, viewer: User) -> bool:
    """On n'écrit plus à un compte désactivé ; un groupe reste toujours ouvert (RG-54)."""
    return conversation.is_group or other(conversation, viewer).is_active


def ago(value: datetime | None, now: datetime | None = None) -> str:
    """Durée courte depuis une date : « à l'instant », « 7 min », « 3 h », « 2 j », « 1 sem. »."""
    if value is None:
        return ""
    seconds = max(0, int(((now or utcnow()) - value).total_seconds()))
    if seconds < 60:
        return "à l'instant"
    if seconds < 3600:
        return f"{seconds // 60} min"
    if seconds < 86400:
        return f"{seconds // 3600} h"
    if seconds < 7 * 86400:
        return f"{seconds // 86400} j"
    return f"{seconds // (7 * 86400)} sem."


def presence(user: User, now: datetime | None = None) -> str:
    """« En ligne », « En ligne il y a 7 min », ou rien si on ne l'a jamais vu (RG-52)."""
    if not user.is_active:
        return "Compte désactivé"
    if user.last_seen_at is None:
        return ""
    now = now or utcnow()
    if (now - user.last_seen_at).total_seconds() < ONLINE_SECONDS:
        return "En ligne"
    return f"En ligne il y a {ago(user.last_seen_at, now)}"


def status_line(conversation: Conversation, viewer: User, now: datetime | None = None) -> str:
    """Sous-titre de l'en-tête : présence de l'autre, ou participants du groupe."""
    if not conversation.is_group:
        return presence(other(conversation, viewer), now)
    names = [m.user.first_name for m in conversation.members if m.user_id != viewer.id]
    return ", ".join(["Toi", *names])


# --- Lecture et non-lus (RG-50, RG-51) ---------------------------------------


def unread_count(conversation: Conversation, viewer: User) -> int:
    member = membership(conversation, viewer)
    if member is None:
        return 0
    return sum(
        1
        for m in conversation.messages
        if m.author_id != viewer.id and m.id > member.last_read_message_id
    )


def mark_read(db: Session, viewer: User, conversation: Conversation) -> None:
    """Le viewer a la conversation sous les yeux : tout est lu (RG-50)."""
    member = membership(conversation, viewer)
    last_id = conversation.messages[-1].id if conversation.messages else 0
    if member is not None and member.last_read_message_id < last_id:
        member.last_read_message_id = last_id
        db.commit()


def seen_by(conversation: Conversation, viewer: User) -> list[User]:
    """Participants qui ont lu mon dernier message, s'il est le dernier du fil (RG-51)."""
    if not conversation.messages or conversation.messages[-1].author_id != viewer.id:
        return []
    last_id = conversation.messages[-1].id
    return [
        m.user
        for m in conversation.members
        if m.user_id != viewer.id and m.last_read_message_id >= last_id
    ]


def _preview(conversation: Conversation, viewer: User) -> str:
    if not conversation.messages:
        return "Groupe créé"
    last = conversation.messages[-1]
    text = " ".join(last.content.split()) or "Photo"
    if last.author_id == viewer.id:
        return f"Toi : {text}"
    if conversation.is_group:
        return f"{last.author.first_name} : {text}"
    return text


def summaries(db: Session, viewer: User) -> list[Summary]:
    """Conversations du viewer, de la plus récente à la plus ancienne.

    Une conversation à deux encore vide (ouverte mais sans message) n'est pas listée.
    """
    result = []
    for conversation in _my_conversations(db, viewer):
        messages = conversation.messages
        if not messages and not conversation.is_group:
            continue
        result.append(
            Summary(
                conversation=conversation,
                title=title(conversation, viewer),
                avatar=avatar(conversation, viewer),
                preview=_preview(conversation, viewer),
                unread=unread_count(conversation, viewer),
                activity=messages[-1].created_at if messages else conversation.created_at,
            )
        )
    result.sort(key=lambda s: (s.activity, s.conversation.id), reverse=True)
    return result


def unread_summaries(db: Session, viewer: User) -> list[Summary]:
    """Conversations avec du non-lu : une ligne chacune dans la cloche (RG-50)."""
    return [s for s in summaries(db, viewer) if s.unread]


def thread_version(conversation: Conversation, viewer: User, now: datetime | None = None) -> str:
    """Empreinte du fil affiché : s'il n'a pas bougé, le rafraîchissement ne renvoie rien."""
    state = (
        [(m.id, m.updated_at) for m in conversation.messages],
        [(m.user_id, m.last_read_message_id) for m in conversation.members],
        status_line(conversation, viewer, now),
        can_write(conversation, viewer),
    )
    return hashlib.sha1(repr(state).encode()).hexdigest()[:12]


# --- Conversations (RG-46, RG-53) --------------------------------------------


def direct_key(a: int, b: int) -> str:
    return f"{min(a, b)}:{max(a, b)}"


def contacts(db: Session, viewer: User) -> list[User]:
    """Membres à qui le viewer peut écrire : les membres actifs, sauf lui."""
    return [m for m in users_service.active_members(db) if m.id != viewer.id]


def open_direct(db: Session, viewer: User, other_id: int) -> Conversation:
    """Conversation à deux avec ce membre, créée si elle n'existe pas encore (RG-46)."""
    key = direct_key(viewer.id, other_id)
    existing = db.scalar(select(Conversation).where(Conversation.direct_key == key))
    if existing is not None and membership(existing, viewer) is not None:
        return existing
    target = users_service.get_active_member(db, other_id)
    if target is None or target.id == viewer.id or not viewer.is_member:
        raise NotFound()
    conversation = Conversation(is_group=False, direct_key=key, creator_id=viewer.id)
    conversation.members = [
        ConversationMember(user_id=viewer.id),
        ConversationMember(user_id=target.id),
    ]
    db.add(conversation)
    db.commit()
    return conversation


def clean_group_name(name: str) -> str:
    name = " ".join((name or "").split())
    if not name:
        raise Invalid("Donne un nom au groupe.")
    if len(name) > NAME_MAX:
        raise Invalid(f"Le nom du groupe ne doit pas dépasser {NAME_MAX} caractères.")
    return name


def create_group(db: Session, viewer: User, name: str, member_ids: list[int]) -> Conversation:
    name = clean_group_name(name)
    allowed = {m.id for m in contacts(db, viewer)}
    chosen = [i for i in dict.fromkeys(member_ids) if i in allowed]
    if not chosen:
        raise Invalid("Choisis au moins une personne.")
    conversation = Conversation(is_group=True, name=name, creator_id=viewer.id)
    conversation.members = [ConversationMember(user_id=i) for i in [viewer.id, *chosen]]
    db.add(conversation)
    db.commit()
    return conversation


def rename_group(db: Session, viewer: User, conversation: Conversation, name: str) -> None:
    if conversation.creator_id != viewer.id:
        raise Forbidden()
    conversation.name = clean_group_name(name)
    db.commit()


def addable(db: Session, conversation: Conversation) -> list[User]:
    present = {m.user_id for m in conversation.members}
    return [m for m in users_service.active_members(db) if m.id not in present]


def add_member(db: Session, conversation: Conversation, user_id: int) -> None:
    """Tout participant peut ajouter un membre actif. Le nouveau voit tout l'historique,
    mais rien ne lui est compté comme non lu (RG-53)."""
    if user_id not in {m.id for m in addable(db, conversation)}:
        raise Invalid("Cette personne ne peut pas être ajoutée.")
    last_id = conversation.messages[-1].id if conversation.messages else 0
    conversation.members.append(ConversationMember(user_id=user_id, last_read_message_id=last_id))
    db.commit()


def remove_member(db: Session, viewer: User, conversation: Conversation, user_id: int) -> None:
    """Seul le créateur retire quelqu'un ; pour partir soi-même, c'est leave() (RG-53)."""
    if conversation.creator_id != viewer.id:
        raise Forbidden()
    target = next((m for m in conversation.members if m.user_id == user_id), None)
    if target is None or user_id == viewer.id:
        raise NotFound()
    conversation.members.remove(target)
    db.commit()


def leave(db: Session, viewer: User, conversation: Conversation) -> None:
    """Quitter un groupe. Le créateur passe la main au plus ancien ; un groupe vide disparaît."""
    paths = _drop_member(db, conversation, viewer.id)
    db.commit()
    _delete_photos(paths)


def _drop_member(db: Session, conversation: Conversation, user_id: int) -> list[str | None]:
    """Retire un participant d'un groupe. Renvoie les photos à effacer si le groupe disparaît."""
    conversation.members = [m for m in conversation.members if m.user_id != user_id]
    if not conversation.members:
        paths = [m.image_path for m in conversation.messages]
        db.delete(conversation)
        return paths
    if conversation.creator_id == user_id:
        conversation.creator_id = conversation.members[0].user_id
    return []


def _delete_photos(paths: list[str | None]) -> None:
    for path in paths:
        images.delete_image(path, root=settings.private_media_dir)


# --- Messages (RG-48, RG-49) -------------------------------------------------


def clean_content(content: str, allow_empty: bool = False) -> str:
    text = (content or "").replace("\r\n", "\n").strip()
    if not text and not allow_empty:
        raise Invalid("Le message ne peut pas être vide.")
    if len(text) > CONTENT_MAX:
        raise Invalid(f"Le message ne doit pas dépasser {CONTENT_MAX} caractères.")
    return text


def send(
    db: Session,
    viewer: User,
    conversation: Conversation,
    content: str,
    photo: UploadFile | None = None,
) -> Message:
    """Envoie un message : du texte, une photo, ou les deux."""
    if not can_write(conversation, viewer):
        raise Invalid("Ce compte est désactivé : tu ne peux plus lui écrire.")
    with_photo = images.has_file(photo)
    text = clean_content(content, allow_empty=with_photo)
    image_path = None
    if with_photo:
        image_path = images.save_image(
            photo, PHOTO_DIR, images.MESSAGE_MAX_SIDE, root=settings.private_media_dir
        )
    message = Message(author_id=viewer.id, content=text, image_path=image_path)
    conversation.messages.append(message)
    db.flush()
    membership(conversation, viewer).last_read_message_id = message.id
    db.commit()
    return message


def edit_message(db: Session, message: Message, content: str) -> None:
    """Modifie le texte. Un message avec photo peut rester sans texte."""
    message.content = clean_content(content, allow_empty=message.image_path is not None)
    message.updated_at = utcnow()
    db.commit()


def delete_message(db: Session, message: Message) -> None:
    """Supprime le message sans laisser de trace, photo comprise (RG-49)."""
    path = message.image_path
    message.conversation.messages.remove(message)
    db.commit()
    _delete_photos([path])


# --- Suppression d'un compte (RG-41, RG-54) ----------------------------------


def purge_member(db: Session, member: User) -> list[str | None]:
    """Efface la trace d'un membre dans les messages privés, avant la suppression du compte.

    Ses conversations à deux disparaissent en entier ; dans les groupes, ses messages sont
    supprimés et il est retiré. Renvoie les photos à effacer une fois la transaction validée.
    """
    paths: list[str | None] = []
    for conversation in _my_conversations(db, member):
        if conversation.is_group:
            paths += _drop_member(db, conversation, member.id)
        else:
            paths += [m.image_path for m in conversation.messages]
            db.delete(conversation)
    db.flush()
    # Ses messages restants : ceux des groupes où il est encore, ou qu'il avait quittés.
    for message in db.scalars(select(Message).where(Message.author_id == member.id)).all():
        paths.append(message.image_path)
        message.conversation.messages.remove(message)
    db.flush()
    return paths


def delete_photos(paths: list[str | None]) -> None:
    _delete_photos(paths)
