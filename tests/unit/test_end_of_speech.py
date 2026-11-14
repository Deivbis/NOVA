from nova.voice import Decision, EndOfSpeechDetector

LOUD = 0.1
QUIET = 0.001


def feed_all(detector, values):
    return [detector.feed(value) for value in values]


def test_quiet_room_continues_until_the_timeout():
    decisions = feed_all(EndOfSpeechDetector(), [QUIET] * 59)

    assert set(decisions) == {Decision.CONTINUE}


def test_no_speech_after_the_timeout():
    decisions = feed_all(EndOfSpeechDetector(), [QUIET] * 60)

    assert decisions[-1] == Decision.NO_SPEECH
    assert set(decisions[:-1]) == {Decision.CONTINUE}


def test_speech_followed_by_silence_ends_the_utterance():
    decisions = feed_all(EndOfSpeechDetector(), [LOUD] * 5 + [QUIET] * 12)

    assert decisions[-1] == Decision.SPEECH_ENDED
    assert set(decisions[:-1]) == {Decision.CONTINUE}


def test_a_short_blip_is_not_speech():
    decisions = feed_all(EndOfSpeechDetector(), [LOUD] + [QUIET] * 59)

    assert decisions[-1] == Decision.NO_SPEECH


def test_isolated_loud_frames_do_not_add_up():
    decisions = feed_all(EndOfSpeechDetector(), [LOUD, QUIET] * 30)

    assert decisions[-1] == Decision.NO_SPEECH


def test_short_pauses_do_not_end_the_utterance():
    values = [LOUD] * 5 + [QUIET] * 8 + [LOUD] * 3 + [QUIET] * 12

    decisions = feed_all(EndOfSpeechDetector(), values)

    assert decisions[-1] == Decision.SPEECH_ENDED
    assert set(decisions[:-1]) == {Decision.CONTINUE}


def test_continuous_speech_stops_at_the_maximum_duration():
    decisions = feed_all(EndOfSpeechDetector(), [LOUD] * 200)

    assert decisions[-1] == Decision.MAX_DURATION
    assert set(decisions[:-1]) == {Decision.CONTINUE}


def test_a_noisy_room_raises_the_threshold():
    detector = EndOfSpeechDetector()

    feed_all(detector, [0.015] * 5)

    assert detector.speech_started is False

    feed_all(detector, [0.3] * 5)

    assert detector.speech_started is True


def test_peak_level_is_tracked():
    detector = EndOfSpeechDetector()

    feed_all(detector, [QUIET, 0.2, QUIET])

    assert detector.peak_rms == 0.2


def test_speech_from_the_first_frame_is_detected():
    decisions = feed_all(EndOfSpeechDetector(), [0.03] * 20 + [QUIET] * 12)

    assert decisions[-1] == Decision.SPEECH_ENDED


def test_soft_speech_in_a_quiet_room_is_detected():
    values = [QUIET] * 3 + [0.02] * 10 + [QUIET] * 12

    decisions = feed_all(EndOfSpeechDetector(), values)

    assert decisions[-1] == Decision.SPEECH_ENDED


def test_soft_speech_from_the_start_with_a_pause_is_detected():
    values = [0.02] * 3 + [0.004] * 2 + [0.02] * 10 + [QUIET] * 12

    decisions = feed_all(EndOfSpeechDetector(), values)

    assert decisions[-1] == Decision.SPEECH_ENDED


def test_noise_floor_is_the_quietest_level_seen():
    detector = EndOfSpeechDetector()

    feed_all(detector, [0.002] * 3)

    assert detector.noise_floor == 0.002