from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.security import current_member, get_csrf_token, verify_csrf
from app.services.purchases import (
    NotPurchaserError,
    NotReservantError,
    cancel_purchase,
    mark_purchased,
)
from app.services.reservations import IsRecipientError, cancel_reservation, reserve_gift
from app.services.visibility import GiftNotFoundError, get_visible_gift
from app.templating import templates

router = APIRouter()


def _fragment_reservation(request: Request, membre: User, db: Session, gift_id: int):
    vue = get_visible_gift(db, membre, gift_id)
    return templates.TemplateResponse(
        request,
        "gifts/_reservation.html",
        {"csrf_token": get_csrf_token(request), "membre": membre, "vue": vue},
    )


@router.post("/cadeaux/{gift_id}/reserver", dependencies=[Depends(verify_csrf)])
def reserver(
    gift_id: int,
    request: Request,
    membre: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    """RG-26 (US-18)."""
    try:
        reserve_gift(db, membre, gift_id)
    except GiftNotFoundError as exc:
        raise HTTPException(status_code=404) from exc
    except IsRecipientError as exc:
        raise HTTPException(status_code=403) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _fragment_reservation(request, membre, db, gift_id)


@router.post("/cadeaux/{gift_id}/annuler-reservation", dependencies=[Depends(verify_csrf)])
def annuler_reservation(
    gift_id: int,
    request: Request,
    membre: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    """RG-27 (US-18)."""
    try:
        cancel_reservation(db, membre, gift_id)
    except GiftNotFoundError as exc:
        raise HTTPException(status_code=404) from exc
    except IsRecipientError as exc:
        raise HTTPException(status_code=403) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _fragment_reservation(request, membre, db, gift_id)


@router.post("/cadeaux/{gift_id}/acheter", dependencies=[Depends(verify_csrf)])
def marquer_achete(
    gift_id: int,
    request: Request,
    membre: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    """RG-28 (US-19)."""
    try:
        mark_purchased(db, membre, gift_id)
    except GiftNotFoundError as exc:
        raise HTTPException(status_code=404) from exc
    except (IsRecipientError, NotReservantError) as exc:
        raise HTTPException(status_code=403) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _fragment_reservation(request, membre, db, gift_id)


@router.post("/cadeaux/{gift_id}/annuler-achat", dependencies=[Depends(verify_csrf)])
def annuler_achat(
    gift_id: int,
    request: Request,
    membre: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    """RG-29 (US-19)."""
    try:
        cancel_purchase(db, membre, gift_id)
    except GiftNotFoundError as exc:
        raise HTTPException(status_code=404) from exc
    except (IsRecipientError, NotPurchaserError) as exc:
        raise HTTPException(status_code=403) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _fragment_reservation(request, membre, db, gift_id)
