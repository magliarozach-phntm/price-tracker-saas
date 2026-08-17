from datetime import datetime, UTC
from zoneinfo import ZoneInfo

from app.web.flash import pop_flash


def convert_to_local(
    dt,
    timezone_name: str,
):
    if dt is None:
        return None

    return dt.astimezone(
        ZoneInfo(timezone_name)
    )


def relative_time(dt):
    if dt is None:
        return "Never"

    now = datetime.now(UTC)
    delta = now - dt

    seconds = int(delta.total_seconds())

    if seconds < 60:
        return "Just now"

    minutes = seconds // 60

    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"

    hours = minutes // 60

    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"

    days = hours // 24

    if days < 7:
        return f"{days} day{'s' if days != 1 else ''} ago"

    weeks = days // 7

    if weeks < 5:
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"

    return dt.strftime("%b %d, %Y")


def template_context(
    request=None,
    current_user=None,
    **kwargs,
):
    timezone_name = (
        current_user.timezone
        if current_user is not None
        else "America/New_York"
    )

    def local_time(dt):
        return convert_to_local(
            dt,
            timezone_name,
        )

    context = {
        "year": datetime.now().year,
        "app_name": "📈 MAG PriceWatch",
        "app_tagline": "SaaS Price Monitoring Platform",
        "current_user": current_user,
        "local_time": local_time,
        "relative_time": relative_time,
        **kwargs,
    }

    if request is not None:
        context["flash"] = pop_flash(
            request
        )

    return context