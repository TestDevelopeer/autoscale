from decimal import Decimal

from terminal_drivers import parse_cas_frame, parse_keli_modbus_response


def test_keli_parser_weight():
    reading = parse_keli_modbus_response("ST 00015000")
    assert reading.weight == Decimal("15000")


def test_cas_parser_stable():
    reading = parse_cas_frame("ST     15230 kg")
    assert reading.stable is True
    assert reading.weight == Decimal("15230")
