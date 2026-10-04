"""A failing optional section after the image must not discard the whole map."""

import logging
import struct

import pytest
from vacuum_map_parser_base.config.color import ColorsPalette
from vacuum_map_parser_base.config.image_config import ImageConfig
from vacuum_map_parser_base.config.size import Sizes

from vacuum_map_parser_viomi.map_data_parser import ViomiMapDataParser

MAP_ID = 0x1234


def _parser() -> ViomiMapDataParser:
    return ViomiMapDataParser(ColorsPalette(), Sizes(), [], ImageConfig(), [])


def _raw_with_bad_charge_station_magic() -> bytes:
    """An empty, valid 'history' section followed by a 'charge_station' with a wrong magic.

    The first section's magic doubles as the map id, so a magic mismatch can only
    happen from the second section on (as seen on viomi.vacuum.v8).
    """
    feature_flags = ViomiMapDataParser.FEATURE_HISTORY | ViomiMapDataParser.FEATURE_CHARGE_STATION
    history = struct.pack("<III", MAP_ID, 0, 0)  # magic, unknown, history_count
    charge_station = struct.pack("<I", 0xDEAD)  # wrong magic
    return struct.pack("<I", feature_flags) + history + charge_station


def test_bad_trailing_section_is_ignored_with_a_warning(caplog):
    with caplog.at_level(logging.WARNING):
        map_data = _parser().parse(_raw_with_bad_charge_station_magic())

    assert map_data.path is not None  # what was parsed before the failure is kept
    assert map_data.charger is None
    assert "section charge_station" in caplog.text
    assert "magic check failed" in caplog.text


def test_strict_mode_still_raises():
    with pytest.raises(ValueError, match="magic check failed"):
        _parser().parse(_raw_with_bad_charge_station_magic(), strict=True)
