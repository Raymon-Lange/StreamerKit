from __future__ import annotations

from models.player import LineupSwap, Recommendation

TREND_BUCKET_SCORES = {
    "HOT": 85.0,
    "WARM": 70.0,
    "NEUTRAL": 50.0,
    "COLD": 25.0,
    "UNKNOWN": 35.0,
}

INTENT_WEIGHT_DEFAULTS = {
    "waiver": {
        "current_performance": 45.0,
        "current_year_rankings": 40.0,
        "dynasty_rankings": 15.0,
    },
    "team_eval": {
        "current_performance": 30.0,
        "current_year_rankings": 25.0,
        "dynasty_rankings": 45.0,
    },
}


def _rank_to_score(rank: int | None, max_rank: int) -> float | None:
    if rank is None:
        return None
    if rank <= 0:
        return None
    clamped = min(rank, max_rank)
    return ((max_rank - clamped + 1) / max_rank) * 100.0


def _average(values: list[float | None]) -> float | None:
    points = [value for value in values if value is not None]
    if not points:
        return None
    return sum(points) / len(points)


def build_hitter_weight_profile(
    intent: str,
    override: dict[str, float] | None = None,
) -> dict[str, float]:
    base = INTENT_WEIGHT_DEFAULTS.get(intent, INTENT_WEIGHT_DEFAULTS["waiver"]).copy()
    if override:
        for key in ("current_performance", "current_year_rankings", "dynasty_rankings"):
            if key in override and override[key] is not None:
                base[key] = float(override[key])

    floor_total = sum(max(0.0, value) for value in base.values())
    if floor_total <= 0:
        return INTENT_WEIGHT_DEFAULTS.get(intent, INTENT_WEIGHT_DEFAULTS["waiver"]).copy()
    return {key: max(0.0, value) for key, value in base.items()}


def evaluate_weighted_hitter(
    *,
    intent: str,
    trend_label: str,
    current_year_ranks: list[int | None],
    dynasty_ranks: list[int | None],
    weight_profile: dict[str, float] | None = None,
) -> tuple[Recommendation, dict]:
    trend_score = TREND_BUCKET_SCORES.get(trend_label, TREND_BUCKET_SCORES["UNKNOWN"])
    raw_current_year_score = _average([_rank_to_score(rank, 300) for rank in current_year_ranks])
    raw_dynasty_score = _average([_rank_to_score(rank, 400) for rank in dynasty_ranks])
    current_year_score = raw_current_year_score if raw_current_year_score is not None else 0.0
    dynasty_score = raw_dynasty_score if raw_dynasty_score is not None else 0.0

    bucket_scores: dict[str, float] = {
        "current_performance": trend_score,
        "current_year_rankings": current_year_score,
        "dynasty_rankings": dynasty_score,
    }

    weights = build_hitter_weight_profile(intent=intent, override=weight_profile)
    active_weight_total = sum(weight for weight in weights.values())
    if active_weight_total <= 0:
        active_weight_total = 1.0

    effective_weights = {
        key: (weight / active_weight_total) * 100.0
        for key, weight in weights.items()
    }

    composite = 0.0
    for key, score in bucket_scores.items():
        composite += score * (effective_weights[key] / 100.0)
    composite = round(composite, 1)

    if intent == "team_eval":
        if composite >= 88:
            action = "AUTO-START / BUILD AROUND"
        elif composite >= 75:
            action = "START"
        elif composite >= 62:
            action = "HOLD / MATCHUP START"
        elif composite >= 50:
            action = "BENCH / DEPTH"
        elif composite >= 40:
            action = "HOLD / DYNASTY VALUE"
        else:
            action = "SHOP / REPLACE"
    else:
        if composite >= 85:
            action = "MUST ADD"
        elif composite >= 72:
            action = "WIN-NOW ADD"
        elif composite >= 60:
            action = "ADD IF NEED FIT"
        elif composite >= 48:
            action = "WATCHLIST / STASH"
        elif composite >= 38:
            action = "SHORT-TERM STREAM"
        else:
            action = "PASS"

    reason = (
        f"Weighted {intent} score {composite:.1f} "
        f"(performance {trend_score:.1f}, "
        f"current-year {f'{raw_current_year_score:.1f}' if raw_current_year_score is not None else 'N/A'}, "
        f"dynasty {f'{raw_dynasty_score:.1f}' if raw_dynasty_score is not None else 'N/A'})"
    )
    recommendation = Recommendation(action=action, reason=reason, score=composite)
    detail = {
        "bucket_scores": bucket_scores,
        "configured_weights": weights,
        "effective_weights": effective_weights,
        "composite_score": composite,
    }
    return recommendation, detail


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


def evaluate_daily_hitter(redraft_rank: int | None, trend_label: str) -> Recommendation:
    """
    Short-term lineup evaluation (day-of / next 2-3 days).
    Trend is the primary driver; rank adds a small bonus.
    """
    _TREND_BASE = {"HOT": 75, "WARM": 55, "NEUTRAL": 40, "COLD": 20, "UNKNOWN": 35}
    base = _TREND_BASE.get(trend_label, 35)

    if redraft_rank is not None:
        if redraft_rank <= 15:
            base += 20
        elif redraft_rank <= 40:
            base += 15
        elif redraft_rank <= 80:
            base += 10
        elif redraft_rank <= 150:
            base += 5

    score = min(base, 100)

    rank_str = f"ranked #{redraft_rank}" if redraft_rank else "unranked"

    if score >= 85:
        return Recommendation("AUTO-START", f"Hot form + elite rank ({rank_str})", score)
    if score >= 70:
        return Recommendation("START", f"Strong recent performance ({rank_str})", score)
    if score >= 55:
        return Recommendation("START / MATCHUP", f"Decent form, use in good matchups ({rank_str})", score)
    if score >= 35:
        return Recommendation("BENCH", f"Marginal — form or rank not there ({rank_str})", score)
    return Recommendation("SIT", f"Cold and low priority ({rank_str})", score)


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


_BENCH_SLOTS = {"BE", "IL", "IL10", "IL15", "IL60", "NA"}


def find_lineup_upgrades(
    rows: list,
    min_score_gap: float = 10.0,
) -> list[LineupSwap]:
    """
    rows: list of (PlayerRecord, redraft_rank, dynasty_rank, TrendSummary, Recommendation, lineup_slot)
    lineup_slot is the ESPN lineupSlot string (e.g. "C", "OF", "BE").
    A bench player can only replace an active player if the bench player is eligible
    for the slot the active player currently occupies.
    """
    active = [(p, trend, rec, slot) for p, _, _, trend, rec, slot in rows if slot not in _BENCH_SLOTS and slot]
    bench = [(p, trend, rec) for p, _, _, trend, rec, slot in rows if slot in _BENCH_SLOTS or not slot]

    upgrades: list[LineupSwap] = []
    for bench_player, bench_trend, bench_rec in bench:
        bench_eligible = set(bench_player.positions)
        best: LineupSwap | None = None

        for active_player, active_trend, active_rec, active_slot in active:
            if active_slot not in bench_eligible:
                continue
            gap = bench_rec.score - active_rec.score
            if gap < min_score_gap:
                continue
            if best is None or gap > best.score_gap:
                best = LineupSwap(
                    start=bench_player,
                    sit=active_player,
                    slot=active_slot,
                    start_rec=bench_rec,
                    sit_rec=active_rec,
                    score_gap=gap,
                    start_trend=bench_trend,
                    sit_trend=active_trend,
                )

        if best:
            upgrades.append(best)

    return sorted(upgrades, key=lambda x: -x.score_gap)
