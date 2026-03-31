from __future__ import annotations

from models.player import Recommendation


def evaluate_roster_hitter(redraft_rank: int | None, dynasty_rank: int | None, trend_label: str) -> Recommendation:
    if redraft_rank is not None and redraft_rank <= 15:
        if dynasty_rank is not None and dynasty_rank <= 40:
            return Recommendation("AUTO-START / BUILD AROUND", "Elite in redraft and dynasty", 100)
        return Recommendation("AUTO-START", "Clear top-end redraft bat", 95)

    if redraft_rank is not None and redraft_rank <= 40:
        return Recommendation("START", "Strong everyday hitter profile", 85)

    if redraft_rank is not None and redraft_rank <= 80:
        if trend_label == "HOT":
            return Recommendation("START", "Midrange bat with strong recent form", 78)
        return Recommendation("HOLD / MATCHUP START", "Useful starter depending on lineup fit", 70)

    if redraft_rank is not None and redraft_rank <= 150:
        if trend_label == "HOT":
            return Recommendation("BENCH / STREAM", "Depth bat worth rotating in while hot", 60)
        return Recommendation("BENCH / DEPTH", "Rosterable depth, but not a must-start", 50)

    if dynasty_rank is not None and dynasty_rank <= 150:
        return Recommendation("HOLD / DYNASTY VALUE", "Long-term value outpaces redraft value", 45)

    if trend_label == "HOT":
        return Recommendation("STREAM / WATCHLIST", "Recent production deserves attention", 35)

    return Recommendation("SHOP / REPLACE", "Lowest-value roster spot to upgrade", 20)


def evaluate_free_agent_hitter(redraft_rank: int | None, dynasty_rank: int | None, trend_label: str) -> Recommendation:
    if redraft_rank is not None and redraft_rank <= 100 and dynasty_rank is not None and dynasty_rank <= 150:
        return Recommendation("MUST ADD", "Strong current and long-term value", 100)
    if redraft_rank is not None and redraft_rank <= 140:
        return Recommendation("WIN-NOW ADD", "Redraft profile is strong enough to help now", 88)
    if dynasty_rank is not None and dynasty_rank <= 180 and trend_label in {"HOT", "WARM"}:
        return Recommendation("STASH / UPSIDE ADD", "Dynasty value plus current momentum", 80)
    if redraft_rank is not None and redraft_rank <= 220 and trend_label == "HOT":
        return Recommendation("ADD IF NEED FIT", "Riding the bat is reasonable here", 70)
    if dynasty_rank is not None and dynasty_rank <= 250:
        return Recommendation("WATCHLIST", "Worth monitoring more than blind adding", 55)
    if trend_label == "HOT":
        return Recommendation("SHORT-TERM STREAM", "Trend is interesting but rank support is thin", 45)
    return Recommendation("PASS", "Low-priority waiver option", 10)
