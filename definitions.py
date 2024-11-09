import dataclasses
from enum import Enum
from gettext import translation
from pathlib import Path

ROOT_DIR = Path(__file__).parent
TEMPLATES_DIR = ROOT_DIR / "templates"
TRANSLATION_DIR = ROOT_DIR / "translations"
TRANSLATIONS = dict()
TRANSLATION_CLASSES = dict()


class Currency(Enum):
    CZK = "CZK"
    EUR = "EUR"


for subdir in TRANSLATION_DIR.iterdir():
    TRANSLATIONS[subdir.name] = translation(
        "app", TRANSLATION_DIR.absolute(), [subdir.name]
    )


def _(string: str, lang: str) -> str:
    translation_ = TRANSLATIONS.get(lang)
    if not translation_:
        return string
    return translation_.gettext(string)


@dataclasses.dataclass
class TranslationClass:
    _lang: str

    def __getattr__(self, item):
        return _(item, self._lang)


for lang in TRANSLATIONS:
    TRANSLATION_CLASSES[lang] = TranslationClass(_lang=lang)
