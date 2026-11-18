"""Mentions « @Prénom » dans les commentaires et notifications associées (RG-42 à RG-45),
et notifications de nouveau cadeau (RG-57).

La lecture des notifications d'un membre passe par visibility.my_notifications.
"""

from markupsafe import Markup, escape
from sqlalchemy.orm import Session

from app.models import Comment, Gift, Notification, User, utcnow
from app.services import users as users_service
from app.services.text import fold


def mentionable(db: Session, gift: Gift) -> list[User]:
    """Membres que l'on peut mentionner dans le fil d'un cadeau (RG-43).

    Le destinataire en est exclu : il ne voit pas ce fil, et une notification lui
    révélerait qu'on parle d'un de ses cadeaux.
    """
    return [m for m in users_service.active_members(db) if m.id != gift.recipient_id]


def split(content: str, members: list[User]) -> list[tuple[str, User | None]]:
    """Découpe un message en morceaux (texte, None) et (mention telle que saisie, membre).

    Une mention est un « @ » suivi d'un prénom complet, sans tenir compte de la casse ni
    des accents. « @Bobby » ne mentionne pas Bob, et « a@bob.fr » ne mentionne personne.
    """
    names = sorted(members, key=lambda m: len(m.first_name), reverse=True)
    parts: list[tuple[str, User | None]] = []
    start = 0
    i = 0
    while i < len(content):
        found = None
        if content[i] == "@" and (i == 0 or not content[i - 1].isalnum()):
            for member in names:
                end = i + 1 + len(member.first_name)
                typed = content[i + 1 : end]
                if len(typed) != len(member.first_name) or typed != typed.strip():
                    continue
                if fold(typed) != fold(member.first_name):
                    continue
                if end < len(content) and content[end].isalnum():
                    continue
                found = (member, end)
                break
        if found is None:
            i += 1
            continue
        member, end = found
        if start < i:
            parts.append((content[start:i], None))
        parts.append((content[i:end], member))
        start = i = end
    if start < len(content):
        parts.append((content[start:], None))
    return parts


def mentioned(content: str, members: list[User]) -> list[User]:
    """Membres mentionnés dans le message, sans doublon."""
    seen: dict[int, User] = {}
    for _text, member in split(content, members):
        if member is not None:
            seen.setdefault(member.id, member)
    return list(seen.values())


def render_mentions(content: str, members: list[User] | None) -> Markup:
    """Filtre Jinja : le message échappé, avec les mentions mises en valeur."""
    out = Markup("")
    for text, member in split(content or "", members or []):
        if member is None:
            out += escape(text)
        else:
            out += Markup('<span class="mention">@{}</span>').format(member.first_name)
    return out


def sync(db: Session, comment: Comment, gift: Gift) -> None:
    """Aligne les notifications d'un commentaire sur ses mentions (RG-42, RG-44).

    À appeler avant le commit, à la création comme à la modification. On ne se
    notifie pas soi-même, et le destinataire du cadeau n'est jamais notifié.
    """
    wanted = {
        m.id for m in mentioned(comment.content, mentionable(db, gift)) if m.id != comment.author_id
    }
    for notification in list(comment.notifications):
        if notification.user_id in wanted:
            wanted.discard(notification.user_id)
        else:
            comment.notifications.remove(notification)
    for user_id in sorted(wanted):
        comment.notifications.append(Notification(user_id=user_id))


def notify_new_gift(db: Session, gift: Gift) -> None:
    """Prévient les membres qui peuvent voir un cadeau qui vient d'être créé (RG-57).

    À appeler avant le commit. L'auteur n'est pas notifié, et le destinataire d'une
    suggestion non plus : il ne doit jamais apprendre qu'on lui en a fait une (RG-30).
    """
    for member in users_service.active_members(db):
        if member.id not in (gift.author_id, gift.recipient_id):
            gift.notifications.append(Notification(user_id=member.id))


def mark_read(db: Session, notifications: list[Notification]) -> None:
    now = utcnow()
    changed = False
    for notification in notifications:
        if notification.read_at is None:
            notification.read_at = now
            changed = True
    if changed:
        db.commit()
