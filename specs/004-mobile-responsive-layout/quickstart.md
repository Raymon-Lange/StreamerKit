# Quickstart: Verifying the Responsive Layout

## Start the dev server

```bash
cd frontend
npm run dev
# Web UI available at http://localhost:9472 (or Vite's default port)
```

## Test the layout

### Small screen (< 1024px)
1. Open browser DevTools → toggle device toolbar (or drag browser window narrow).
2. Set viewport to **375px** width (typical phone).
3. Confirm: all 7 cards render in a **single column**, top to bottom.
4. Confirm: no horizontal scrollbar or overflow.
5. Confirm: DailyBrief stats show in a **2-column** internal grid.

### Breakpoint transition
1. Set viewport to **1023px** width.
2. Confirm: still one-column (stacked) layout.
3. Resize to **1024px**.
4. Confirm: layout switches to two-column — DailyBrief and Profile span full width, remaining cards appear two-per-row.

### Desktop (≥ 1024px)
1. Set viewport to **1280px** or full window.
2. Confirm: DailyBrief and Profile are full-width.
3. Confirm: Streamers, TomorrowStreamers, RecentDrops, Optimizer, WeeklyScores appear two per row.
4. Confirm: DailyBrief stats show in a **4-column** internal grid.
