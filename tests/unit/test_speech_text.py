from nova.voice.speech_text import clean_for_speech, prepare_speech


def test_plain_text_without_final_punctuation_is_one_chunk():
    assert prepare_speech("Buenos días, Jefe") == ["Buenos días, Jefe"]


def test_sentences_are_split():
    text = (
        "Esta es la primera frase de prueba. "
        "Esta es la segunda frase de prueba."
    )

    assert prepare_speech(text) == [
        "Esta es la primera frase de prueba.",
        "Esta es la segunda frase de prueba.",
    ]


def test_short_sentences_are_merged():
    result = prepare_speech("¿Cómo estás? Muy bien, gracias. ¡Qué bueno!")

    assert result == ["¿Cómo estás? Muy bien, gracias. ¡Qué bueno!"]


def test_line_breaks_split_the_text():
    text = (
        "Primera línea de la lista completa.\n"
        "Segunda línea de la lista completa."
    )

    assert len(prepare_speech(text)) == 2


def test_markdown_emphasis_is_removed():
    assert prepare_speech("**Hola** `código` __texto__") == [
        "Hola código texto"
    ]


def test_headers_and_bullets_are_removed():
    text = (
        "# Título importante del texto\n"
        "- Uno de la lista larga\n"
        "* Dos de la lista larga"
    )

    spoken = " ".join(prepare_speech(text))

    assert "#" not in spoken
    assert "- " not in spoken
    assert "*" not in spoken
    assert "Título importante" in spoken


def test_code_blocks_are_not_read():
    text = (
        "Mira esto:\n```python\nprint(1)\n```\n"
        "Listo, Jefe, ya está todo hecho."
    )

    spoken = " ".join(prepare_speech(text))

    assert "print" not in spoken
    assert "Listo, Jefe" in spoken


def test_markdown_links_keep_only_the_text():
    text = "[NOVA](https://x.com) es genial para trabajar."

    assert prepare_speech(text) == ["NOVA es genial para trabajar."]


def test_bare_urls_become_the_word_enlace():
    spoken = prepare_speech(
        "Visita https://example.com/abc ahora mismo por favor."
    )[0]

    assert "enlace" in spoken
    assert "https" not in spoken


def test_emojis_are_removed_but_spanish_punctuation_stays():
    spoken = " ".join(
        prepare_speech("¡Hola Deibis! 😊 ¿En qué puedo ayudarte hoy? 🌞")
    )

    assert "😊" not in spoken
    assert "🌞" not in spoken
    assert "¡Hola" in spoken
    assert "¿En qué" in spoken


def test_decimal_numbers_do_not_split_sentences():
    text = "El valor es 3.14 aproximadamente en total."

    assert prepare_speech(text) == [text]


def test_empty_or_symbol_only_text_gives_no_chunks():
    assert prepare_speech("😊 🌞") == []
    assert prepare_speech("   ") == []
    assert prepare_speech("```x```") == []


def test_ellipsis_does_not_leave_tiny_chunks():
    text = "Bueno... déjame pensar en ello un momento."

    assert prepare_speech(text) == [text]


def test_long_text_without_punctuation_is_cut():
    chunks = prepare_speech("palabra " * 80)

    assert len(chunks) >= 2
    assert all(len(chunk) <= 240 for chunk in chunks)


def test_long_text_is_cut_at_commas():
    chunks = prepare_speech("Uno, dos, tres, " * 30)

    assert len(chunks) >= 2
    assert all(len(chunk) <= 240 for chunk in chunks)


def test_numbered_lists_keep_their_numbers():
    text = (
        "1. Abre el navegador ahora mismo.\n"
        "2. Busca música para programar."
    )

    result = prepare_speech(text)

    assert len(result) == 2
    assert result[0].startswith("1.")


def test_a_short_first_sentence_joins_the_next_one():
    result = prepare_speech("Sí.\nClaro que sí, Jefe, enseguida lo hago.")

    assert result == ["Sí. Claro que sí, Jefe, enseguida lo hago."]


def test_clean_for_speech_removes_emphasis():
    assert clean_for_speech("*cursiva* y **negrita**") == "cursiva y negrita"


def test_a_single_word_is_spoken():
    assert prepare_speech("Hola") == ["Hola"]