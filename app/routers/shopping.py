"""Listes de courses (RG-59 à RG-61) : HTTP et templates seulement.

Chaque action marche en formulaire classique (redirection) et en HTMX : la zone des
articles est alors renvoyée seule, sans recharger la page.
"""

from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import Invalid
from app.models import ShoppingList, User
from app.security import current_member, flash
from app.services import shopping as shopping_service
from app.web import fragment, is_htmx, redirect, render

router = APIRouter()


def _items_context(shopping_list: ShoppingList, error: str | None = None, values=None) -> dict:
    return {
        "shopping_list": shopping_list,
        "pending": shopping_service.pending(shopping_list),
        "done": shopping_service.done(shopping_list),
        "error": error,
        "values": values or {},
    }


def _list_page(
    request: Request,
    user: User,
    shopping_list: ShoppingList,
    error: str | None = None,
    values: dict | None = None,
    rename_error: str | None = None,
    status_code: int = 200,
):
    context = _items_context(shopping_list, error, values)
    context["rename_error"] = rename_error
    return render(request, "shopping/list.html", context, user=user, status_code=status_code)


def _after_change(request: Request, user: User, shopping_list: ShoppingList):
    """Réponse après une action sur les articles : fragment HTMX ou redirection."""
    if is_htmx(request):
        return fragment(request, "shopping/_items.html", _items_context(shopping_list))
    return redirect(f"/courses/{shopping_list.id}")


# --- Toutes les listes ----------------------------------------------------------


@router.get("/courses")
def lists_page(
    request: Request, user: User = Depends(current_member), db: Session = Depends(get_db)
):
    return render(
        request,
        "shopping/index.html",
        {"lists": shopping_service.all_lists(db), "error": None, "name": ""},
        user=user,
    )


@router.post("/courses")
def create_list(
    request: Request,
    name: str = Form(""),
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    try:
        shopping_list = shopping_service.create_list(db, user, name)
    except Invalid as exc:
        return render(
            request,
            "shopping/index.html",
            {"lists": shopping_service.all_lists(db), "error": exc.message, "name": name},
            user=user,
            status_code=422,
        )
    return redirect(f"/courses/{shopping_list.id}")


# --- Une liste ------------------------------------------------------------------


@router.get("/courses/{list_id}")
def list_page(
    request: Request,
    list_id: int,
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    return _list_page(request, user, shopping_service.get_list(db, list_id))


@router.post("/courses/{list_id}/renommer")
def rename_list(
    request: Request,
    list_id: int,
    name: str = Form(""),
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    shopping_list = shopping_service.get_list(db, list_id)
    try:
        shopping_service.rename_list(db, shopping_list, name)
    except Invalid as exc:
        return _list_page(request, user, shopping_list, rename_error=exc.message, status_code=422)
    flash(request, "Liste renommée.")
    return redirect(f"/courses/{list_id}")


@router.post("/courses/{list_id}/supprimer")
def delete_list(
    request: Request,
    list_id: int,
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    shopping_list = shopping_service.get_list(db, list_id)
    name = shopping_list.name
    shopping_service.delete_list(db, shopping_list)
    flash(request, f"Liste « {name} » supprimée.")
    return redirect("/courses")


# --- Articles -------------------------------------------------------------------


@router.post("/courses/{list_id}/articles")
def add_item(
    request: Request,
    list_id: int,
    name: str = Form(""),
    quantity: str = Form(""),
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    shopping_list = shopping_service.get_list(db, list_id)
    try:
        shopping_service.add_item(db, user, shopping_list, name, quantity)
    except Invalid as exc:
        values = {"name": name, "quantity": quantity}
        if is_htmx(request):
            context = _items_context(shopping_list, exc.message, values)
            return fragment(request, "shopping/_items.html", context, status_code=422)
        return _list_page(request, user, shopping_list, exc.message, values, status_code=422)
    return _after_change(request, user, shopping_list)


@router.post("/courses/{list_id}/articles/{item_id}/cocher")
def toggle_item(
    request: Request,
    list_id: int,
    item_id: int,
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    shopping_list = shopping_service.get_list(db, list_id)
    shopping_service.toggle_item(db, user, shopping_service.get_item(db, shopping_list, item_id))
    return _after_change(request, user, shopping_list)


@router.post("/courses/{list_id}/articles/{item_id}/supprimer")
def delete_item(
    request: Request,
    list_id: int,
    item_id: int,
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    shopping_list = shopping_service.get_list(db, list_id)
    shopping_service.delete_item(db, shopping_service.get_item(db, shopping_list, item_id))
    return _after_change(request, user, shopping_list)


@router.post("/courses/{list_id}/vider")
def clear_checked(
    request: Request,
    list_id: int,
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    shopping_list = shopping_service.get_list(db, list_id)
    shopping_service.clear_checked(db, shopping_list)
    return _after_change(request, user, shopping_list)
