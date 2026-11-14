from nova.core import Identity
from nova.personality import PROFILES, profile_for


def test_each_identity_has_a_profile():
    assert set(PROFILES) == set(Identity)


def test_prompts_name_the_identity_and_its_gender():
    atlas = profile_for(Identity.ATLAS).system_prompt
    asti = profile_for(Identity.ASTI).system_prompt

    assert "Atlas" in atlas and "masculin" in atlas
    assert "Asti" in asti and "Abi" in asti and "femenin" in asti


def test_prompts_set_the_required_behavior():
    for profile in PROFILES.values():
        for text in ("Jefe", "Señor", "emojis", "aclaración", "Nunca finjas"):
            assert text in profile.system_prompt


def test_prompts_stay_short():
    for profile in PROFILES.values():
        assert len(profile.system_prompt) <= 700


def test_prompts_have_no_emojis():
    for profile in PROFILES.values():
        for char in profile.system_prompt + profile.confirmation:
            assert ord(char) < 0x1F000
            assert not 0x2600 <= ord(char) <= 0x27BF


def test_confirmations_mention_the_identity():
    assert "Atlas" in profile_for(Identity.ATLAS).confirmation
    assert "Asti" in profile_for(Identity.ASTI).confirmation


def test_profiles_differ():
    atlas = profile_for(Identity.ATLAS)
    asti = profile_for(Identity.ASTI)

    assert atlas.system_prompt != asti.system_prompt
    assert atlas.confirmation != asti.confirmation