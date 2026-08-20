from __future__ import annotations

import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.scores_service import _scoreboard_for_period


def _team(team_id):
    return types.SimpleNamespace(team_id=team_id, team_name=f"Team {team_id}")


def _fake_league(schedule, teams):
    espn_request = types.SimpleNamespace(league_get=lambda params=None: {"schedule": schedule})
    return types.SimpleNamespace(espn_request=espn_request, teams=teams)


def _matchup_entry(period, home_id, away_id=None):
    entry = {
        "matchupPeriodId": period,
        "home": {"teamId": home_id, "totalPoints": 0},
        "winner": "UNDECIDED",
    }
    if away_id is not None:
        entry["away"] = {"teamId": away_id, "totalPoints": 0}
    return entry


class TestScoreboardForPeriod:
    def test_skips_bye_week_matchup_without_crashing(self):
        # Team 3 has a bye in period 1: ESPN's payload omits 'away' entirely.
        schedule = [
            _matchup_entry(1, home_id=1, away_id=2),
            _matchup_entry(1, home_id=3),
        ]
        league = _fake_league(schedule, teams=[_team(1), _team(2), _team(3)])

        matchups = _scoreboard_for_period(league, 1)

        assert len(matchups) == 1
        assert matchups[0].home_team.team_id == 1
        assert matchups[0].away_team.team_id == 2

    def test_filters_to_requested_period_only(self):
        schedule = [
            _matchup_entry(1, home_id=1, away_id=2),
            _matchup_entry(2, home_id=1, away_id=2),
        ]
        league = _fake_league(schedule, teams=[_team(1), _team(2)])

        matchups = _scoreboard_for_period(league, 2)

        assert len(matchups) == 1
