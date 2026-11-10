"""Écran d'accueil : liste des personnes (US-10)."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.security import current_member
from app.services import visibility
from app.web import render

router = APIRouter()


@router.get("/")
def people(request: Request, user: User = Depends(current_member), db: Session = Depends(get_db)):
    return render(
        request,
        "people.html",
        {"people": visibility.people_with_counts(db, user)},
        user=user,
    )
