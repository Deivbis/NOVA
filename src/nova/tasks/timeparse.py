"""Interpreta cuándo en español: «en 10 minutos», «mañana a las 9», «a las 5 pm»."""

import re
from datetime import datetime, timedelta

_F = re.IGNORECASE
_NUM = {
    "un": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
    "quince": 15, "veinte": 20, "treinta": 30,
}
_WORDS = "|".join(_NUM)
_END = r"(?![\wáéíóúñ])"

_REL = re.compile(
    r"\b(?:en|dentro\s+de)\s+(?:(?P<half>media)\s+hora"
    rf"|(?P<n>\d+|{_WORDS})\s+(?P<u>minutos?|horas?|d[ií]as?))\b", _F)
_TIME = re.compile(
    r"\ba\s+las?\s+(?P<h>\d{1,2}|una)(?::(?P<m>\d{2}))?\s*"
    rf"(?P<ap>(?:a\.?\s?m\.?|p\.?\s?m\.?){_END}"
    rf"|de\s+la\s+(?:ma[ñn]ana|tarde|noche|madrugada){_END})?", _F)
_DAY = re.compile(r"\b(?P<d>hoy|pasado\s+ma[ñn]ana|ma[ñn]ana)\b", _F)
_OFFSET = {"hoy": 0, "manana": 1, "pasado manana": 2}


def _title(work: str) -> str:
    text = " ".join(work.split()).strip(" ,.;:")

    return re.sub(r"^(?:que|de|para)\s+", "", text, flags=_F)


def parse_when(
    text: str,
    now: datetime,
) -> tuple[str, datetime | None, str | None]:
    """(título, momento, error). `now` debe tener zona horaria."""
    work = text

    def blank(match: re.Match) -> None:
        nonlocal work
        span = match.end() - match.start()
        work = work[: match.start()] + " " * span + work[match.end():]

    rel = _REL.search(work)

    if rel:
        blank(rel)

        if rel["half"]:
            delta = timedelta(minutes=30)
        else:
            raw = rel["n"].lower()
            n = int(raw) if raw.isdigit() else _NUM[raw]
            unit = rel["u"].lower()
            delta = (
                timedelta(minutes=n) if unit.startswith("min")
                else timedelta(hours=n) if unit.startswith("hora")
                else timedelta(days=n)
            )

        return _title(work), (now + delta).replace(microsecond=0), None

    time_match = _TIME.search(work)

    if time_match:
        blank(time_match)

    day = _DAY.search(work)

    if day:
        blank(day)

    title = _title(work)

    if time_match is None and day is None:
        return title, None, None

    offset = 0

    if day:
        key = " ".join(day["d"].lower().replace("ñ", "n").split())
        offset = _OFFSET[key]

    if time_match is None:
        if offset == 0:
            return title, None, "Dime a qué hora."

        hour, minute, marker, pm, am = 9, 0, True, False, False
    else:
        hour = 1 if time_match["h"].lower() == "una" else int(time_match["h"])
        minute = int(time_match["m"] or 0)
        ap = (
            (time_match["ap"] or "").lower().replace("ñ", "n")
            .replace(".", "").replace(" ", "")
        )
        marker = bool(ap)
        pm = ap.startswith("p") or "tarde" in ap or "noche" in ap
        am = not pm and bool(ap)

        if hour > 23 or minute > 59:
            return title, None, "Esa hora no es válida."

        if pm and hour < 12:
            hour += 12
        elif pm and "noche" in ap and hour == 12:
            hour = 0
        elif am and hour == 12:
            hour = 0

    base = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if day:
        base += timedelta(days=offset)

        if base <= now:
            return title, None, "Esa hora ya pasó."
    elif base <= now:
        alt = base + timedelta(hours=12)

        if not marker and 1 <= hour <= 11 and alt > now:
            base = alt
        else:
            base += timedelta(days=1)

    return title, base, None