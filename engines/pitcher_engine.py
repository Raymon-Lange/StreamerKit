from __future__ import annotations

from models.player import Recommendation

TIER_EMOJI = {
    "Auto-Start": "🟢",
    "Probably Start": "🟡",
    "Questionable Start": "🟠",
    "Do Not Start": "🔴",
    "Not Ranked": "⚪",
}

TIER_REC = {
    "Auto-Start": "PICKUP — Auto-Start, high-confidence",
    "Probably Start": "PICKUP — Probable start, solid option",
    "Questionable Start": "CONSIDER — Only if desperate",
    "Do Not Start": "SKIP — Do not start",
    "Not Ranked": "Not in today's Pitcher List post",
}


def streamer_recommendation(tier: str | None) -> Recommendation:
    resolved = tier or "Not Ranked"
    return Recommendation(
        action=TIER_REC.get(resolved, TIER_REC["Not Ranked"]),
        reason=f"Pitcher List tier: {resolved}",
        score={
            "Auto-Start": 100,
            "Probably Start": 80,
            "Questionable Start": 45,
            "Do Not Start": 10,
            "Not Ranked": 5,
        }.get(resolved, 5),
    )
