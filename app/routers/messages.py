"""Messages privés (US-29 à US-35).

Chaque route passe par services/messages.py, qui vérifie que le membre est participant
de la conversation : pour tout autre, la réponse est une erreur 404 (RG-47).

Les vues s'affichent dans la pop-up (fragment HTMX) ou, sans JavaScript, en pleine page.
"""

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import Invalid
from app.models import User
from app.security import current_member
from app.services import messages as messages_service
from app.web import fragment, is_htmx, member_chrome, redirect, render

router = APIRouter()


def _view(request: Request, user: User, name: str, context: dict, status_code: int = 200):
    """Une vue de la messagerie : fragment pour la pop-up, page entière sinon."""
    ctx = {**context, "user": user}
    if is_htmx(request):
        return fragment(request, f"messages/{name}", ctx, status_code=status_code)
    ctx["view"] = f"messages/{name}"
    return render(request, "messages/page.html", ctx, user=user, status_code=status_code)


def _thread_context(user: User, conversation, error: str | None = None) -> dict:
    return {
        "conversation": conversation,
        "messages": conversation.messages,
        "seen_by": messages_service.seen_by(conversation, user),
        "status": messages_service.status_line(conversation, user),
        "version": messages_service.thread_version(conversation, user),
        "can_write": messages_service.can_write(conversation, user),
        "error": error,
    }


def _conversation(request: Request, db: Session, user: User, conversation, status_code: int = 200):
    messages_service.mark_read(db, user, conversation)
    context = {
        **_thread_context(user, conversation),
        "title": messages_service.title(conversation, user),
        "face": messages_service.avatar(conversation, user),
    }
    return _view(request, user, "_conversation.html", context, status_code)


def _thread(request: Request, user: User, conversation, error=None, status_code: int = 200):
    context = {**_thread_context(user, conversation, error), "user": user, "oob": True}
    return fragment(request, "messages/_thread.html", context, status_code=status_code)


def _new(request: Request, db: Session, user: User, error=None, form=None, status_code=200):
    context = {
        "contacts": messages_service.contacts(db, user),
        "error": error,
        "form": form or {"name": "", "members": []},
    }
    return _view(request, user, "_new.html", context, status_code)


def _settings(request: Request, db: Session, user: User, conversation, error=None, status_code=200):
    context = {
        "conversation": conversation,
        "addable": messages_service.addable(db, conversation),
        "is_creator": conversation.creator_id == user.id,
        "error": error,
    }
    return _view(request, user, "_settings.html", context, status_code)


def _edit(request: Request, user: User, message, content: str, error=None, status_code=200):
    context = {"message": message, "content": content, "error": error}
    return _view(request, user, "_edit.html", context, status_code)


# --- Liste, bulle, nouvelle conversation -------------------------------------


@router.get("/messages")
def messages_list(
    request: Request, user: User = Depends(current_member), db: Session = Depends(get_db)
):
    return _view(request, user, "_list.html", {"summaries": messages_service.summaries(db, user)})


@router.get("/messages/bulle")
def messages_bubble(request: Request, user: User = Depends(current_member)):
    """Bulle « Messages » et compteur de la cloche, rechargés régulièrement (RG-55)."""
    return fragment(request, "messages/_bubble.html", {**member_chrome(user), "oob": True})


@router.get("/messages/nouveau")
def new_conversation(
    request: Request, user: User = Depends(current_member), db: Session = Depends(get_db)
):
    return _new(request, db, user)


@router.post("/messages/avec/{other_id}")
def open_direct(
    request: Request,
    other_id: int,
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    conversation = messages_service.open_direct(db, user, other_id)
    if is_htmx(request):
        return _conversation(request, db, user, conversation)
    return redirect(f"/messages/{conversation.id}")


@router.post("/messages/groupes")
def create_group(
    request: Request,
    name: str = Form(""),
    members: list[int] = Form([]),
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    try:
        conversation = messages_service.create_group(db, user, name, members)
    except Invalid as exc:
        form = {"name": name, "members": members}
        return _new(request, db, user, error=exc.message, form=form, status_code=422)
    if is_htmx(request):
        return _conversation(request, db, user, conversation)
    return redirect(f"/messages/{conversation.id}")


# --- Un message : photo, modification, suppression ---------------------------


@router.get("/messages/photos/{message_id}")
def message_photo(
    message_id: int, user: User = Depends(current_member), db: Session = Depends(get_db)
):
    """Photo d'un message, servie aux seuls participants (RG-47)."""
    path = messages_service.photo_file(db, user, message_id)
    return FileResponse(
        path, media_type="image/webp", headers={"Cache-Control": "private, max-age=86400"}
    )


@router.get("/messages/m/{message_id}/modifier")
def edit_message_form(
    request: Request,
    message_id: int,
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    message = messages_service.get_own_message(db, user, message_id)
    return _edit(request, user, message, message.content)


@router.post("/messages/m/{message_id}/modifier")
def edit_message(
    request: Request,
    message_id: int,
    content: str = Form(""),
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    message = messages_service.get_own_message(db, user, message_id)
    try:
        messages_service.edit_message(db, message, content)
    except Invalid as exc:
        return _edit(request, user, message, content, error=exc.message, status_code=422)
    if is_htmx(request):
        return _conversation(request, db, user, message.conversation)
    return redirect(f"/messages/{message.conversation_id}")


@router.post("/messages/m/{message_id}/supprimer")
def delete_message(
    request: Request,
    message_id: int,
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    message = messages_service.get_own_message(db, user, message_id)
    conversation = message.conversation
    messages_service.delete_message(db, message)
    if is_htmx(request):
        return _thread(request, user, conversation)
    return redirect(f"/messages/{conversation.id}")


# --- Une conversation --------------------------------------------------------


@router.get("/messages/{conversation_id}")
def conversation_page(
    request: Request,
    conversation_id: int,
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    conversation = messages_service.get_conversation(db, user, conversation_id)
    return _conversation(request, db, user, conversation)


@router.get("/messages/{conversation_id}/fil")
def conversation_thread(
    request: Request,
    conversation_id: int,
    v: str = "",
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    """Fil rechargé toutes les 5 secondes tant que la conversation est affichée (RG-55).

    L'avoir sous les yeux vaut lecture. Si rien n'a changé, la réponse est vide (204).
    """
    conversation = messages_service.get_conversation(db, user, conversation_id)
    messages_service.mark_read(db, user, conversation)
    if v and v == messages_service.thread_version(conversation, user):
        return Response(status_code=204)
    return _thread(request, user, conversation)


@router.post("/messages/{conversation_id}")
def send_message(
    request: Request,
    conversation_id: int,
    content: str = Form(""),
    photo: UploadFile | None = File(None),
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    conversation = messages_service.get_conversation(db, user, conversation_id)
    try:
        messages_service.send(db, user, conversation, content, photo)
    except Invalid as exc:
        if is_htmx(request):
            return _thread(request, user, conversation, error=exc.message, status_code=422)
        context = {
            **_thread_context(user, conversation, exc.message),
            "title": messages_service.title(conversation, user),
            "face": messages_service.avatar(conversation, user),
        }
        return _view(request, user, "_conversation.html", context, status_code=422)
    messages_service.mark_read(db, user, conversation)
    if is_htmx(request):
        return _thread(request, user, conversation)
    return redirect(f"/messages/{conversation_id}")


# --- Réglages d'un groupe (RG-53) --------------------------------------------


@router.get("/messages/{conversation_id}/reglages")
def group_settings(
    request: Request,
    conversation_id: int,
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    conversation = messages_service.get_group(db, user, conversation_id)
    return _settings(request, db, user, conversation)


def _after_settings(request: Request, db: Session, user: User, conversation):
    if is_htmx(request):
        return _settings(request, db, user, conversation)
    return redirect(f"/messages/{conversation.id}/reglages")


@router.post("/messages/{conversation_id}/nom")
def rename_group(
    request: Request,
    conversation_id: int,
    name: str = Form(""),
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    conversation = messages_service.get_group(db, user, conversation_id)
    try:
        messages_service.rename_group(db, user, conversation, name)
    except Invalid as exc:
        db.refresh(conversation)
        return _settings(request, db, user, conversation, error=exc.message, status_code=422)
    return _after_settings(request, db, user, conversation)


@router.post("/messages/{conversation_id}/membres")
def add_group_member(
    request: Request,
    conversation_id: int,
    user_id: int = Form(0),
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    conversation = messages_service.get_group(db, user, conversation_id)
    try:
        messages_service.add_member(db, conversation, user_id)
    except Invalid as exc:
        return _settings(request, db, user, conversation, error=exc.message, status_code=422)
    return _after_settings(request, db, user, conversation)


@router.post("/messages/{conversation_id}/membres/{member_id}/retirer")
def remove_group_member(
    request: Request,
    conversation_id: int,
    member_id: int,
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    conversation = messages_service.get_group(db, user, conversation_id)
    messages_service.remove_member(db, user, conversation, member_id)
    return _after_settings(request, db, user, conversation)


@router.post("/messages/{conversation_id}/quitter")
def leave_group(
    request: Request,
    conversation_id: int,
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    conversation = messages_service.get_group(db, user, conversation_id)
    messages_service.leave(db, user, conversation)
    if is_htmx(request):
        return _view(
            request, user, "_list.html", {"summaries": messages_service.summaries(db, user)}
        )
    return redirect("/messages")
