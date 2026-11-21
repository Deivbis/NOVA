"""Habla mientras el modelo aún escribe (P-014)."""

import queue
import re

from nova.voice.speech_text import prepare_speech

MIN_CHARS = 25
_BOUNDARY = re.compile(r"[.!?…]+[\"')\]»]*\s|\n")


class SpeechStream:
    def __init__(
        self, service, generation: int, feed: "queue.Queue[str | None]"
    ) -> None:
        self._service = service
        self._generation = generation
        self._feed = feed
        self._raw = ""
        self._text = ""
        self._in_code = False
        self._closed = False

    def feed(self, delta: str) -> None:
        if self._closed or not self._service.is_current(self._generation):
            return

        self._raw += delta
        self._scan(final=False)
        self._emit(final=False)

    def end(self, extra: str = "") -> None:
        if self._closed:
            return

        if self._service.is_current(self._generation):
            self._raw += extra
            self._scan(final=True)
            self._emit(final=True)

        self._closed = True
        self._feed.put(None)

    def cancel(self) -> None:
        if self._closed:
            return

        self._closed = True
        self._feed.put(None)
        self._service.cancel_stream(self._generation)

    def _scan(self, final: bool) -> None:
        raw = self._raw

        while raw:
            i = raw.find("```")

            if i >= 0:
                if not self._in_code:
                    self._text += raw[:i]

                raw = raw[i + 3:]
                self._in_code = not self._in_code
                continue

            keep = 0 if final else min(2, len(raw) - len(raw.rstrip("`")))
            head = raw[: len(raw) - keep]

            if not self._in_code:
                self._text += head

            raw = raw[len(raw) - keep:]
            break

        self._raw = raw

    def _emit(self, final: bool) -> None:
        text = self._text

        if final:
            complete, rest = text, ""
        else:
            matches = list(_BOUNDARY.finditer(text))
            cut = (
                matches[-1].end()
                if matches and matches[-1].end() >= MIN_CHARS
                else 0
            )
            complete, rest = text[:cut], text[cut:]

        self._text = rest

        for sentence in prepare_speech(complete):
            self._feed.put(sentence)