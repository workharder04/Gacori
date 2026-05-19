# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Kumo Matcha Tea** — an interactive single-page product showcase. The entire application lives in one file: `index.html`. There is no build step, no package manager, and no test framework. Open `index.html` directly in a browser to run it.

## Development

Since there is no build toolchain, just open `index.html` in a browser:

```bash
# Quick local server (Python)
python3 -m http.server 8080

# Or with Node
npx serve .
```

No linting or test commands exist. The project uses CDN-hosted dependencies:
- **Tailwind CSS** (utility classes via CDN — limited utility classes are used; most styling is custom CSS)
- **Font Awesome 6.6** (icons)
- **Google Fonts** — Inter + Noto Serif SC

## Architecture

The entire application is a self-contained IIFE in the `<script>` block of `index.html`. There are three layers:

### 1. Design Token System (CSS → JS)
CSS custom properties on `:root` (`--hue`, `--sat`, `--bg`, `--pkg`, `--pkg-dark`, `--pkg-light`, `--accent`, `--accent-s`) drive every color in the UI. `applyPalette(flavor)` recomputes and sets all of these at runtime, plus directly mutates SVG gradient stop colors via `setAttribute('stop-color', ...)`. This means adding a new visual element requires updating both the CSS token consumers and the `applyPalette` function.

### 2. FLAVORS Array — Single Source of Truth
All flavor data lives in the `FLAVORS` array at the top of the script. Each entry carries: display name, price, label, hue/sat for token generation, individual SVG gradient stop colors (sky, three mountain layers, birds), and emoji. Adding a new flavor means adding one entry here — the carousel, palette, and label all derive from it automatically.

### 3. Arc Carousel
Cards are positioned on an elliptical arc using trigonometry:
- `arcGeom()` computes radii `Rh` (horizontal) and `Rv` (vertical) from the live track width, keeping layout responsive without media queries.
- `positionArc(fi, withTransition)` iterates all cards and computes `translateX/Y`, `scale`, `opacity`, and `rotateY` from each card's angular distance from the active fractional index `fi`. Shortest-path wrapping handles the circular sequence.
- `fracIdx` holds a fractional index during drag; `current` holds the snapped integer after release.
- Drag commits (left or right) if `dragDeltaX` exceeds `COMMIT_THRESHOLD` (44 px). One pixel maps to `1/DRAG_PX_PER_STEP` (1/90) of a card step.

### 4. SVG Package Illustration
The tea bag artwork is an inline SVG with named `<linearGradient>` elements (IDs: `skyG`, `m1G`, `m2G`, `m3G`). Their `<stop>` elements are referenced by ID and mutated directly by `applyPalette`. The bamboo and grass `fill` attributes are recomputed from `hue`/`sat` on each flavor change.

## Key Conventions

- **All state is module-level** inside the IIFE: `current`, `fracIdx`, `cartCount`, `isDragging`, `dragStartX`, `dragDeltaX`.
- `window.selectFlavor` and `window.toggleCart` are intentionally exposed for inline `onclick` attributes in the HTML.
- The `arc-track` element is observed with `ResizeObserver` — `positionArc` is called on every resize to recompute positions without breakpoints.
- Transition is toggled per-call: `withTransition = false` during live drag (no CSS transition lag), `true` after snap.
- Mobile breakpoint at 480 px hides nav links, socials, and location chip text via `@media`.
