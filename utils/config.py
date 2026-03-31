from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date

from dotenv import load_dotenv

load_dotenv()


@dataclass(slots=True)
class AppConfig:
    league_id: int = int(os.getenv("LEAGUE_ID", 0) or 0)
    team_id: int = int(os.getenv("TEAM_ID", 0) or 0)
    year: int = date.today().year
    espn_s2: str = os.getenv("ESPN_S2", "")
    espn_swid: str = os.getenv("ESPN_SWID", "")
