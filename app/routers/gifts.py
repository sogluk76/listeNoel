"""Cadeaux : liste d'une personne, détail, ajout, modification, suppression,
réservation et achat (US-11 à US-19)."""

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import Invalid
from app.models import User
from app.security import current_member, flash
from app.services import gifts as gifts_service
from app.services import images, reservations, visibility
from app.services import notifications as notifications_service
from app.services import users as users_service
from app.web import fragment, is_htmx, redirect, render

router = APIRouter()

SORTS = (visibility.SORT_NAME, visibility.SORT_PRICE, visibility.SORT_STATUS)


def _to_int(value: str | None) -> int | None:
    try:
        return int(value) if value not in (None, "") else None
    except ValueError:
        return None


# --- Liste de cadeaux d'une personne (US-13, US-14) --------------------------


@router.get("/personnes/{person_id}")
def person_gifts(
    request: Request,
    person_id: int,
    q: str = "",
    tri: str = visibility.SORT_NAME,
    sens: str = "asc",
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    person = visibility.get_person(db, person_id)
    is_me = person.id == user.id
    if tri not in SORTS or (is_me and tri == visibility.SORT_STATUS):
        tri = visibility.SORT_NAME
    views = visibility.list_gifts(db, user, person, q, tri, descending=(sens == "desc"))
    context = {
        "person": person,
        "is_me": is_me,
        "views": views,
        "q": q,
        "tri": tri,
        "sens": "desc" if sens == "desc" else "asc",
    }
    if is_htmx(request):
        return fragment(request, "_gift_items.html", context)
    return render(request, "gift_list.html", context, user=user)


# --- Ajout (US-11, US-12) ----------------------------------------------------


def _form_page(request, db, user, *, gift=None, values=None, errors=None, status_code=200):
    others = [m for m in users_service.active_members(db) if m.id != user.id]
    return render(
        request,
        "gift_form.html",
        {"gift": gift, "values": values or {}, "errors": errors or {}, "others": others},
        user=user,
        status_code=status_code,
    )


@router.get("/cadeaux/nouveau")
def new_gift_form(
    request: Request,
    pour: str = "",
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    values = {}
    target = users_service.get_active_member(db, _to_int(pour))
    if target is not None and target.id != user.id:
        values = {"suggest": True, "recipient_id": target.id}
    return _form_page(request, db, user, values=values)


@router.post("/cadeaux")
def create_gift(
    request: Request,
    name: str = Form(""),
    suggest: str = Form(""),
    price: str = Form(""),
    url: str = Form(""),
    recipient_id: str = Form(""),
    image: UploadFile | None = File(None),
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    is_suggestion = bool(suggest)
    data, errors = gifts_service.validate(name, price, url)
    recipient = gifts_service.resolve_recipient(db, user, is_suggestion, _to_int(recipient_id))
    if recipient is None:
        errors["recipient_id"] = "Choisis la personne à qui tu penses."

    image_path = None
    if not errors and images.has_file(image):
        try:
            image_path = images.save_image(image, "gifts", images.GIFT_MAX_SIDE)
        except Invalid as exc:
            errors["image"] = exc.message

    if errors:
        values = {
            "name": name,
            "price": price,
            "url": url,
            "suggest": is_suggestion,
            "recipient_id": _to_int(recipient_id),
        }
        return _form_page(request, db, user, values=values, errors=errors, status_code=422)

    gifts_service.create(db, user, recipient, data, image_path)
    flash(request, "Cadeau ajouté.")
    return redirect(f"/personnes/{recipient.id}")


# --- Détail (US-15) ----------------------------------------------------------


@router.get("/cadeaux/{gift_id}")
def gift_detail(
    request: Request,
    gift_id: int,
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    gift = visibility.get_gift(db, user, gift_id)
    # Ouvrir la fiche vaut lecture de la notification « nouveau cadeau » (RG-57).
    notifications_service.mark_read(
        db, [n for n in visibility.my_notifications(db, user) if n.gift_id == gift.id]
    )
    return render(request, "gift_detail.html", {"view": visibility.build_view(user, gift)}, user)


# --- Modification (US-16) ----------------------------------------------------


@router.get("/cadeaux/{gift_id}/modifier")
def edit_gift_form(
    request: Request,
    gift_id: int,
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    gift = visibility.get_gift(db, user, gift_id)
    gifts_service.require_author(user, gift)
    values = {
        "name": gift.name,
        "price": f"{gift.price:.2f}".replace(".", ",") if gift.price is not None else "",
        "url": gift.url or "",
    }
    return _form_page(request, db, user, gift=gift, values=values)


@router.post("/cadeaux/{gift_id}/modifier")
def edit_gift(
    request: Request,
    gift_id: int,
    name: str = Form(""),
    price: str = Form(""),
    url: str = Form(""),
    remove_image: str = Form(""),
    image: UploadFile | None = File(None),
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    gift = visibility.get_gift(db, user, gift_id)
    gifts_service.require_author(user, gift)
    data, errors = gifts_service.validate(name, price, url)

    new_image = None
    if not errors and images.has_file(image):
        try:
            new_image = images.save_image(image, "gifts", images.GIFT_MAX_SIDE)
        except Invalid as exc:
            errors["image"] = exc.message

    if errors:
        values = {"name": name, "price": price, "url": url}
        return _form_page(
            request, db, user, gift=gift, values=values, errors=errors, status_code=422
        )

    gifts_service.update(db, user, gift, data, new_image, remove_image=bool(remove_image))
    flash(request, "Cadeau modifié.")
    return redirect(f"/cadeaux/{gift.id}")


# --- Suppression (US-17) -----------------------------------------------------


@router.post("/cadeaux/{gift_id}/supprimer")
def delete_gift(
    request: Request,
    gift_id: int,
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    gift = visibility.get_gift(db, user, gift_id)
    recipient_id = gift.recipient_id
    gifts_service.delete_by_author(db, user, gift)
    # Même message et même écran en suppression définitive ou douce (RG-22).
    flash(request, "Cadeau supprimé.")
    return redirect(f"/personnes/{recipient_id}")


# --- Réservation et achat (US-18, US-19) -------------------------------------


def _reservation_action(request: Request, db: Session, user: User, gift_id: int, action, done: str):
    gift = visibility.get_gift_with_secrets(db, user, gift_id)
    try:
        action(db, user, gift)
        flash(request, done)
    except Invalid as exc:
        flash(request, exc.message, "error")
    return redirect(f"/cadeaux/{gift_id}")


@router.post("/cadeaux/{gift_id}/reserver")
def reserve(
    request: Request,
    gift_id: int,
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    return _reservation_action(
        request, db, user, gift_id, reservations.reserve, "C'est noté, tu t'en occupes."
    )


@router.post("/cadeaux/{gift_id}/annuler-reservation")
def cancel_reservation(
    request: Request,
    gift_id: int,
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    return _reservation_action(
        request, db, user, gift_id, reservations.cancel, "Réservation annulée."
    )


@router.post("/cadeaux/{gift_id}/acheter")
def mark_bought(
    request: Request,
    gift_id: int,
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    return _reservation_action(
        request, db, user, gift_id, reservations.mark_bought, "Cadeau marqué comme acheté."
    )


@router.post("/cadeaux/{gift_id}/annuler-achat")
def cancel_bought(
    request: Request,
    gift_id: int,
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    return _reservation_action(
        request, db, user, gift_id, reservations.cancel_bought, "Achat annulé."
    )
