# Research: Data Source Status Page

## Decision Log

### Where does feed health logic live?

**Decision**: Extract into `services/feed_health_service.py`; both `scripts/show_feed_health.py` and the new route call it.

**Rationale**: `show_feed_health.py` already has the complete logic for querying collector cache freshness and failure records. Duplicating it in a route would violate the constitution's simplicity principle and create two sources of truth. Extracting to a service satisfies Layer Separation (I) — the script and route are both thin callers.

**Alternatives considered**: Inline the logic in the route (rejected — duplication), or have the route shell-exec the script (rejected — brittle, returns text not data).

---

### What does the response cache inspector show?

**Decision**: List all entries in the `response` namespace of the cache store where `(now - cached_at) < ttl_seconds`. Show key name, age in seconds, and remaining TTL in seconds.

**Rationale**: The `response` namespace uses a 30-minute default TTL (1800 s). Entries are keyed by route+params (e.g. `streamers_2026-06-10_all`, `optimizer`). Showing age + remaining TTL tells the operator whether the next UI load will hit cache or re-run the collectors. Expired entries are excluded — they will be pruned on next startup and are not actionable.

**Alternatives considered**: Show all entries including expired (rejected — noise); show entry size/content preview (rejected — out of scope, no immediate value).

---

### How does frontend navigation work?

**Decision**: Add a two-tab header navigation in `App.tsx` using local `useState`. No router library introduced.

**Rationale**: There are only two pages. A full router (React Router) would be an unjustified abstraction (Constitution V). A simple state toggle renders either the dashboard grid or the feed status page, each as a named component group. Deep-linking is not a requirement for this single-user tool.

**Alternatives considered**: React Router with path-based routing (rejected — overkill for 2 tabs, adds dependency); separate HTML page (rejected — breaks SPA build).

---

### New models: where do they live?

**Decision**: `models/feed_health.py` with `@dataclass(slots=True)` types `FeedSource`, `CacheEntry`, `FeedHealthSnapshot`.

**Rationale**: Constitution (II) requires canonical types for inter-module data exchange. Player-domain types in `models/player.py` are unrelated. A new file scoped to this domain keeps the models file small and focused.

**Alternatives considered**: Add to `models/player.py` (rejected — wrong domain); use plain dicts across service/route boundary (rejected — violates Constitution II).
