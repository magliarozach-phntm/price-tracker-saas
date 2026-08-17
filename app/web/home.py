from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.web import templates
from app.web.context import template_context


router = APIRouter()


@router.get("/")
def home(
    request: Request,
):
    if request.session.get("user_id"):
        return RedirectResponse(
            url="/dashboard",
            status_code=303,
        )

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=template_context(
            request=request,
            current_user=None,
        ),
    )