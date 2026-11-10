"""Notifications de mention (US-27, US-28).

La liste passe par visibility.my_notifications : un membre ne reçoit jamais de
notification sur un fil qu'il n'a pas le droit de voir (RG-30, RG-43).
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.security import current_member
from app.services import notifications as notifications_service
from app.services import visibility
from app.web import render

router = APIRouter()

PAGE_SIZE = 50


@router.get("/notifications")
def notifications_page(
    request: Request,
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    """Affiche les notifications, puis les marque toutes comme lues (RG-45)."""
    visible = visibility.my_notifications(db, user)
    items = [(n, n.read_at is None) for n in visible[:PAGE_SIZE]]
    notifications_service.mark_read(db, visible)
    return render(request, "notifications.html", {"items": items}, user=user)
