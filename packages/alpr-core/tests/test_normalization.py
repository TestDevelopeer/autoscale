from alpr_core import normalize_ru_plate


def test_normalize_homoglyphs():
    assert normalize_ru_plate("а123вс77") == "A123BC77"
