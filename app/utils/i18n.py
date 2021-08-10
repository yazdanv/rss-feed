import gettext

from app.core.config import settings


_default_lang = None


def active_translation(lang):
    global _default_lang
    _default_lang = (
        settings.DEFAULT_LANGUAGE if lang not in settings.SUPPORTED_LANGUAGE else lang
    )


def trans(message: str) -> str:
    return gettext.translation(
        "base", localedir="app/locales", languages=[_default_lang]
    ).gettext(message)
