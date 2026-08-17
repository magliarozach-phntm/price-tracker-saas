from fastapi import Request


def add_flash(
    request: Request,
    message: str,
    category: str = "info",
):
    request.session["flash_message"] = {
        "message": message,
        "category": category,
    }


def pop_flash(
    request: Request,
):
    return request.session.pop(
        "flash_message",
        None,
    )