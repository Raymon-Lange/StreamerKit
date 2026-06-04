# Research: Mobile Responsive Card Layout

**Branch**: `004-mobile-responsive-layout` | **Date**: 2026-06-04

## Decisions

### 1. Breakpoint Selection

**Decision**: Use the `lg` breakpoint (1024px) as the threshold for switching from one-column to two-column layout.

**Rationale**:
- The current `md` breakpoint (768px) is too narrow for real-world use. Screens from 768px to ~1024px — tablets in landscape, small laptops, narrow browser windows on desktops — all land in the two-column range, which is cramped at those widths.
- `lg` (1024px) is the industry-standard threshold for "desktop" in responsive design, covering the point where a two-column card layout becomes comfortable without padding pressure.
- Tailwind's named breakpoints are already in the project's config with no custom overrides, so `lg:` is available at zero additional cost.

**Alternatives considered**:
- `md` (768px): Already in use; does not help users on tablets or small laptops (the stated problem).
- `xl` (1280px): Too conservative; would force single-column on most laptops.
- Custom arbitrary value (e.g., `[900px]`): Tailwind supports this but adds a non-standard value with no named semantic meaning.

---

### 2. Full-Width Card Behaviour on Small Screens

**Decision**: Replace bare `col-span-2` on `DailyBrief` and `Profile` with `col-span-1 lg:col-span-2`.

**Rationale**:
- In a `grid-cols-1` layout (i.e., one-column mobile), a `col-span-2` with no mobile override creates an implicit second grid column. This forces horizontal overflow and breaks the stack.
- Adding `col-span-1` as the mobile-default and gating `col-span-2` at `lg:` ensures the cards behave correctly in both layouts: full-width on desktop, full-width (naturally, since there is only one column) on mobile without overflow.

**Alternatives considered**:
- Wrapping full-width cards in a `col-span-full` container: works but adds extra DOM nesting for no benefit.
- Using `w-full` instead of `col-span`: does not fix the implicit column creation in grid context.

---

### 3. DailyBrief Internal Grid

**Decision**: Update the DailyBrief internal stat grid from `md:grid-cols-4` to `lg:grid-cols-4`, keeping `grid-cols-2` as the mobile default.

**Rationale**:
- The internal grid uses the same breakpoint logic as the outer layout. Keeping it at `md:grid-cols-4` while the outer grid switches at `lg:` would create a mismatch: from 768–1023px the outer grid is one column (full-width card) but the internal grid is already in 4-column mode, which is fine visually. However, aligning both to `lg:` keeps the responsive behavior consistent and avoids any edge-case layout issues at medium widths.
- The `grid-cols-2` mobile default gives a reasonable 2-up stat layout at narrow widths.

**Alternatives considered**:
- Leaving the internal grid at `md:grid-cols-4`: technically harmless (the card is full-width from 0–1023px, so the 4-column internal layout triggers at 768px+ regardless), but inconsistent with the outer breakpoint.

---

## Files to Change

| File | Change |
|------|--------|
| `frontend/src/App.tsx` line 17 | `md:grid-cols-2` → `lg:grid-cols-2` |
| `frontend/src/components/DailyBrief.tsx` line 48 | `col-span-2` → `col-span-1 lg:col-span-2` |
| `frontend/src/components/DailyBrief.tsx` line 50 | `md:grid-cols-4` → `lg:grid-cols-4` |
| `frontend/src/components/Profile.tsx` line 30 | `col-span-2` → `col-span-1 lg:col-span-2` |

No backend, API, or data model changes required.
