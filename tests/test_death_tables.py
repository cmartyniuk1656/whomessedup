"""Long sessions must retain later deaths and their complete WCL recaps."""
from unittest.mock import Mock, patch

import pytest

from who_messed_up.api import Fight
from who_messed_up.services.death_tables import fetch_complete_death_table


def fights(count):
    return [Fight(id=i + 1, name="Boss", start=i * 100000, end=i * 100000 + 90000, kill=False)
            for i in range(count)]


def capped_table(counts):
    entries = [dict(fight=fid, id=player, timestamp=(fid - 1) * 100000 + player * 100,
                    killingBlow={"guid": 123}, events=[{"timestamp": (fid - 1) * 100000, "amount": 99}])
               for fid, count in counts.items() for player in range(count)]

    def fetch(*args, fight_ids, start, end, **kwargs):
        # Boundary checks guard against a timestamp-based fix clipping recaps.
        assert start == (min(fight_ids) - 1) * 100000
        assert end == (max(fight_ids) - 1) * 100000 + 90000
        return {"entries": [entry for entry in entries if entry["fight"] in fight_ids][:200]}

    return entries, fetch


def test_recorded_pull_counts_survive_200_death_cutoff():
    # X6FGCJm3pqjQMNdv: original request cuts off at death 6 of pull 11.
    counts = [20, 21, 19, 17, 21, 18, 20, 19, 20, 19, 20, 22, 21, 20, 20, 20, 7]
    expected, fetch = capped_table(dict(enumerate(counts, 1)))
    with patch("who_messed_up.services.death_tables.fetch_table", side_effect=fetch) as request:
        table = fetch_complete_death_table(Mock(), "token", code="REPORT", fights=fights(17))
    assert table["entries"] == expected
    assert len(table["entries"]) == 324
    assert sum(e["fight"] == 11 for e in table["entries"]) == 20
    assert request.call_count == 3


def test_short_reports_keep_single_request_and_recaps():
    expected, fetch = capped_table({1: 20, 2: 19})
    with patch("who_messed_up.services.death_tables.fetch_table", side_effect=fetch) as request:
        result = fetch_complete_death_table(Mock(), "token", code="REPORT", fights=fights(2))
    assert result["entries"] == expected
    assert request.call_count == 1


def test_exact_cap_is_rechecked_without_duplicate_deaths():
    expected, fetch = capped_table({1: 100, 2: 100})
    with patch("who_messed_up.services.death_tables.fetch_table", side_effect=fetch):
        result = fetch_complete_death_table(Mock(), "token", code="REPORT", fights=fights(2))
    assert result["entries"] == expected


def test_nested_saturated_batches_and_empty_pulls():
    expected, fetch = capped_table({1: 190, 2: 0, 3: 190, 4: 190})
    with patch("who_messed_up.services.death_tables.fetch_table", side_effect=fetch):
        result = fetch_complete_death_table(Mock(), "token", code="REPORT", fights=fights(4))
    assert result["entries"] == expected


def test_single_saturated_pull_fails_explicitly_instead_of_truncating():
    _, fetch = capped_table({1: 250})
    with patch("who_messed_up.services.death_tables.fetch_table", side_effect=fetch), pytest.raises(RuntimeError, match="partial report"):
        fetch_complete_death_table(Mock(), "token", code="REPORT", fights=fights(1))


def test_no_fights_does_not_query_unscoped_deaths():
    with patch("who_messed_up.services.death_tables.fetch_table") as request:
        assert fetch_complete_death_table(Mock(), "token", code="REPORT", fights=[]) == {"entries": []}
    request.assert_not_called()
