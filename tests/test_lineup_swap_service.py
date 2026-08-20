from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import collectors.espn as espn_collector
import services.lineup_swap_service as lineup_swap_service
from collectors.espn import EspnContext, EspnWriteError, swap_lineup_slots
from models.player import LineupMove, PlayerRecord
from utils.config import AppConfig


def _fake_context(scoring_period_id=119):
    config = AppConfig(league_id=1568301661, team_id=9, year=2026, espn_s2="s2token", espn_swid="{SWID}")
    league = types.SimpleNamespace(scoringPeriodId=scoring_period_id)
    return EspnContext(league=league, config=config)


def _fake_response(status_code=200, json_data=None):
    return types.SimpleNamespace(
        status_code=status_code,
        text="error body",
        json=lambda: json_data or {"status": "EXECUTED"},
    )


class TestSwapLineupSlots:
    def test_payload_shape(self, monkeypatch):
        captured = {}

        def fake_post(url, params=None, json=None, cookies=None, headers=None, timeout=None):
            captured["url"] = url
            captured["params"] = params
            captured["json"] = json
            captured["cookies"] = cookies
            return _fake_response()

        monkeypatch.setattr(espn_collector.requests, "post", fake_post)

        context = _fake_context()
        moves = [
            LineupMove(player_id=31267, from_slot_id=16, to_slot_id=13),
            LineupMove(player_id=42406, from_slot_id=13, to_slot_id=16),
        ]
        result = swap_lineup_slots(context, team_id=9, moves=moves)

        assert result["status"] == "EXECUTED"
        assert "1568301661" in captured["url"]
        assert "2026" in captured["url"]
        assert captured["json"] == {
            "isLeagueManager": False,
            "teamId": 9,
            "type": "FUTURE_ROSTER",
            "memberId": "{SWID}",
            "scoringPeriodId": 120,
            "executionType": "EXECUTE",
            "items": [
                {"playerId": 31267, "type": "LINEUP", "fromLineupSlotId": 16, "toLineupSlotId": 13},
                {"playerId": 42406, "type": "LINEUP", "fromLineupSlotId": 13, "toLineupSlotId": 16},
            ],
        }
        assert captured["cookies"] == {"espn_s2": "s2token", "SWID": "{SWID}"}

    def test_non_200_raises(self, monkeypatch):
        monkeypatch.setattr(espn_collector.requests, "post", lambda *a, **kw: _fake_response(status_code=400))
        with pytest.raises(EspnWriteError):
            swap_lineup_slots(_fake_context(), team_id=9, moves=[])

    def test_non_executed_status_raises(self, monkeypatch):
        monkeypatch.setattr(
            espn_collector.requests, "post", lambda *a, **kw: _fake_response(json_data={"status": "PENDING"})
        )
        with pytest.raises(EspnWriteError):
            swap_lineup_slots(_fake_context(), team_id=9, moves=[])

    def test_network_failure_raises(self, monkeypatch):
        def raise_conn_error(*a, **kw):
            raise espn_collector.requests.RequestException("boom")

        monkeypatch.setattr(espn_collector.requests, "post", raise_conn_error)
        with pytest.raises(EspnWriteError):
            swap_lineup_slots(_fake_context(), team_id=9, moves=[])


def _player(name, external_id, positions, slot):
    return PlayerRecord(
        name=name,
        normalized_name=name.lower(),
        positions=positions,
        external_id=external_id,
        espn_raw=types.SimpleNamespace(lineupSlot=slot),
    )


class TestSwapPlayers:
    def _patch_roster(self, monkeypatch, players, team_id=9):
        monkeypatch.setattr(lineup_swap_service, "build_context", lambda config: _fake_context())
        monkeypatch.setattr(lineup_swap_service, "get_team", lambda context, team_id=None: types.SimpleNamespace(team_id=team_id))
        monkeypatch.setattr(lineup_swap_service, "get_roster_players", lambda context, team_id=None: players)

    def test_eligible_swap_calls_espn_and_invalidates_cache(self, monkeypatch):
        players = [
            _player("Bench Guy", 1, ["2B", "SS"], "BE"),
            _player("Starter Guy", 2, ["2B", "SS"], "2B"),
        ]
        self._patch_roster(monkeypatch, players)

        write_calls = []
        monkeypatch.setattr(
            lineup_swap_service,
            "swap_lineup_slots",
            lambda context, team_id, moves: write_calls.append((team_id, moves)) or {"status": "EXECUTED"},
        )
        invalidated = []
        monkeypatch.setattr(lineup_swap_service.response_cache, "invalidate_prefix", lambda prefix: invalidated.append(prefix))

        result = lineup_swap_service.swap_players(1, 2, team_id=9)

        assert result.success is True
        assert write_calls  # ESPN write was attempted
        team_id, moves = write_calls[0]
        assert team_id == 9
        assert {(m.player_id, m.from_slot_id, m.to_slot_id) for m in moves} == {(1, 16, 2), (2, 2, 16)}
        assert invalidated == ["my_roster_", "optimizer_"]

    def test_ineligible_swap_never_calls_espn(self, monkeypatch):
        players = [
            _player("DH Only", 1, ["DH"], "BE"),
            _player("Second Baseman", 2, ["2B"], "2B"),
        ]
        self._patch_roster(monkeypatch, players)

        write_calls = []
        monkeypatch.setattr(
            lineup_swap_service, "swap_lineup_slots", lambda *a, **kw: write_calls.append(1) or {"status": "EXECUTED"}
        )

        result = lineup_swap_service.swap_players(1, 2, team_id=9)

        assert result.success is False
        assert "not eligible" in result.message
        assert write_calls == []

    def test_espn_rejection_is_surfaced(self, monkeypatch):
        players = [
            _player("Bench Guy", 1, ["2B"], "BE"),
            _player("Starter Guy", 2, ["2B"], "2B"),
        ]
        self._patch_roster(monkeypatch, players)

        def raise_write_error(*a, **kw):
            raise EspnWriteError("ESPN rejected the swap (HTTP 400): bad request")

        monkeypatch.setattr(lineup_swap_service, "swap_lineup_slots", raise_write_error)

        result = lineup_swap_service.swap_players(1, 2, team_id=9)

        assert result.success is False
        assert "rejected" in result.message

    def test_unknown_player_id_fails_cleanly(self, monkeypatch):
        players = [_player("Only Guy", 1, ["2B"], "2B")]
        self._patch_roster(monkeypatch, players)

        result = lineup_swap_service.swap_players(1, 999, team_id=9)

        assert result.success is False
        assert "Could not find" in result.message

    def test_dry_run_never_calls_espn(self, monkeypatch):
        players = [
            _player("Bench Guy", 1, ["2B"], "BE"),
            _player("Starter Guy", 2, ["2B"], "2B"),
        ]
        self._patch_roster(monkeypatch, players)

        write_calls = []
        monkeypatch.setattr(
            lineup_swap_service, "swap_lineup_slots", lambda *a, **kw: write_calls.append(1) or {"status": "EXECUTED"}
        )

        result = lineup_swap_service.swap_players(1, 2, team_id=9, dry_run=True)

        assert result.success is True
        assert "Dry run" in result.message
        assert write_calls == []
