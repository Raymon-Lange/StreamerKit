from __future__ import annotations

from datetime import date

import requests
import statsapi

from models.player import TrendSummary

CURRENT_YEAR = date.today().year


def get_player_id(name: str, prefer_pitcher: bool = False) -> int | None:
    try:
        results = statsapi.lookup_player(name)
    except Exception:
        return None
    if not results:
        return None

    for player in results:
        abbr = (player.get("primaryPosition") or {}).get("abbreviation", "")
        if prefer_pitcher and abbr in {"SP", "P", "RP"}:
            return player["id"]
        if not prefer_pitcher and abbr not in {"SP", "P", "RP"}:
            return player["id"]
    return results[0].get("id")


def get_hitter_game_log(player_id: int):
    try:
        data = statsapi.get("people", {
            "personIds": player_id,
            "hydrate": f"stats(group=hitting,type=gameLog,season={CURRENT_YEAR})",
        })
    except Exception:
        return []

    people = data.get("people", [])
    if not people:
        return []

    for group in people[0].get("stats", []):
        if group.get("type", {}).get("displayName") == "gameLog":
            return sorted(group.get("splits", []), key=lambda item: item.get("date", ""), reverse=True)
    return []


def summarize_recent_hitting(name: str, trend_games: int = 10) -> TrendSummary:
    player_id = get_player_id(name, prefer_pitcher=False)
    if not player_id:
        return TrendSummary(summary="No MLB trend data found")

    logs = get_hitter_game_log(player_id)[:trend_games]
    if not logs:
        return TrendSummary(summary="No MLB games logged yet this season")

    ab = sum((g.get("stat", {}) or {}).get("atBats", 0) or 0 for g in logs)
    hits = sum((g.get("stat", {}) or {}).get("hits", 0) or 0 for g in logs)
    doubles = sum((g.get("stat", {}) or {}).get("doubles", 0) or 0 for g in logs)
    triples = sum((g.get("stat", {}) or {}).get("triples", 0) or 0 for g in logs)
    hr = sum((g.get("stat", {}) or {}).get("homeRuns", 0) or 0 for g in logs)
    bb = sum((g.get("stat", {}) or {}).get("baseOnBalls", 0) or 0 for g in logs)
    hbp = sum((g.get("stat", {}) or {}).get("hitByPitch", 0) or 0 for g in logs)
    sf = sum((g.get("stat", {}) or {}).get("sacFlies", 0) or 0 for g in logs)
    sb = sum((g.get("stat", {}) or {}).get("stolenBases", 0) or 0 for g in logs)
    runs = sum((g.get("stat", {}) or {}).get("runs", 0) or 0 for g in logs)
    rbi = sum((g.get("stat", {}) or {}).get("rbi", 0) or 0 for g in logs)

    avg = hits / ab if ab else None
    total_bases = (hits - doubles - triples - hr) + doubles * 2 + triples * 3 + hr * 4
    obp_den = ab + bb + hbp + sf
    obp = (hits + bb + hbp) / obp_den if obp_den else None
    slg = total_bases / ab if ab else None
    ops = (obp + slg) if (obp is not None and slg is not None) else None

    label = "NEUTRAL"
    if avg is not None and ops is not None:
        if ops >= 0.950 or (avg >= 0.320 and (hr + sb) >= 3):
            label = "HOT"
        elif ops >= 0.800 or avg >= 0.280:
            label = "WARM"
        elif ops < 0.550 and avg < 0.180:
            label = "COLD"

    summary = (
        f"Last {len(logs)} G: AVG {avg:.3f} / OPS {ops:.3f} / HR {hr} / SB {sb} / RBI {rbi} / R {runs}"
        if avg is not None and ops is not None
        else f"Last {len(logs)} G: no rate stats available"
    )

    return TrendSummary(
        label=label,
        games=len(logs),
        avg=avg,
        ops=ops,
        hr=hr,
        sb=sb,
        rbi=rbi,
        runs=runs,
        summary=summary,
    )


def get_pitcher_game_log(player_id: int):
    try:
        data = statsapi.get("people", {
            "personIds": player_id,
            "hydrate": f"stats(group=pitching,type=gameLog,season={CURRENT_YEAR})",
        })
    except Exception:
        return []

    people = data.get("people", [])
    if not people:
        return []

    for group in people[0].get("stats", []):
        if group.get("type", {}).get("displayName") == "gameLog":
            return sorted(group.get("splits", []), key=lambda item: item.get("date", ""), reverse=True)
    return []


def get_pitcher_stats(name: str):
    player_id = get_player_id(name, prefer_pitcher=True)
    if not player_id:
        return "N/A", "N/A", []

    try:
        season_data = statsapi.player_stat_data(player_id, group="pitching", type="season", season=CURRENT_YEAR)
        season_stats = season_data.get("stats", [])
        season_record = f"{season_stats[0].get('stats', {}).get('wins', 0)}-{season_stats[0].get('stats', {}).get('losses', 0)}" if season_stats else "0-0"
    except Exception:
        season_record = "N/A"

    game_log = get_pitcher_game_log(player_id)
    last_ten = game_log[:10]
    wins = sum(1 for game in last_ten if game.get("stat", {}).get("wins", 0) > 0)
    losses = sum(1 for game in last_ten if game.get("stat", {}).get("losses", 0) > 0)
    last_ten_record = f"{wins}-{losses} (last {len(last_ten)} GS)" if last_ten else "0-0 (0 GS)"

    last_two = []
    for game in game_log[:2]:
        stat = game.get("stat", {})
        opp = game.get("opponent", {}).get("abbreviation", "???")
        matchup = f"vs {opp}" if game.get("isHome", True) else f"@ {opp}"
        result = "W" if stat.get("wins", 0) else "L" if stat.get("losses", 0) else "ND"
        last_two.append({
            "date": game.get("date", "N/A"),
            "matchup": matchup,
            "result": result,
            "ip": stat.get("inningsPitched", "0.0"),
            "h": stat.get("hits", 0),
            "r": stat.get("runs", 0),
            "er": stat.get("earnedRuns", 0),
            "bb": stat.get("baseOnBalls", 0),
            "k": stat.get("strikeOuts", 0),
            "era": stat.get("era", "-.--"),
        })

    return season_record, last_ten_record, last_two


def get_todays_probable_starters() -> set[str]:
    today = date.today().strftime("%Y%m%d")
    url = f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard?dates={today}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return set()

    starters: set[str] = set()
    for event in data.get("events", []):
        for competition in event.get("competitions", []):
            for competitor in competition.get("competitors", []):
                for probable in competitor.get("probables", []):
                    athlete = probable.get("athlete", {})
                    name = athlete.get("displayName") or athlete.get("fullName")
                    if name:
                        starters.add(name)
    return starters
