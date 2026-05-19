# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a single-file, zero-build interactive product page for **kumo • Matcha Tea** — a flavor selector UI where users swipe/drag/keyboard-navigate between tea flavors on a circular arc carousel.

**Everything lives in one file: `index.html`**. There is no package manager, no build step, no test suite, and no linting toolchain. Open `index.html` directly in a browser to run the project.

## Architecture

### Single-file structure

The file is divided into three parts (all inline):
1. **`<style>` block** — CSS custom properties (design tokens) + layout
2. **`<body>`** — Static HTML scaffolding; the arc carousel cards are injected by JS
3. **`<script>` block** — All logic wrapped in an IIFE

### Design token system

Colors are driven by two CSS custom properties set at `:root`:
```css
--hue: 120; --sat: 38;
```
All other color tokens (`--bg`, `--pkg`, `--pkg-dark`, `--pkg-light`, `--accent`, `--accent-s`) are derived from `--hue`/`--sat` via `hsl()` calculations. When the user selects a flavor, `applyPalette()` updates `--hue` and `--sat` on `document.documentElement` along with all six derived tokens, driving a full-page color transition.

### Flavor data

The `FLAVORS` array is the single source of truth. Each entry carries:
- Display metadata: `name`, `price`, `label`, `emoji`
- Palette: `hue`, `sat` (for CSS tokens)
- SVG gradient stop colors: `sky1`, `sky2`, `sun`, `m1a/m1b`, `m2a/m2b`, `m3a/m3b`, `birds`

### Arc carousel

Cards are positioned mathematically on a circular arc using `positionArc(fi, withTransition)`:
- `fi` is a **fractional index** (integer during rest, float during drag)
- Each card's `rel` index is shortest-path-wrapped around `N/2` to handle wrapping
- Position: `tx = Rh * sin(rel * SPREAD)`, `ty = Rv * (cos(rel * SPREAD) - 1)`
- The arc geometry (`Rh`, `Rv`, `SPREAD`) recomputes from live track width via a `ResizeObserver`, so no CSS breakpoints are needed for the carousel

During drag, `fracIdx` is updated live (no transition). On release, `selectFlavor()` snaps to the nearest integer index with `COMMIT_THRESHOLD = 44px`.

### SVG artwork

The tea bag illustration (`#bag-art`) is inline SVG with named gradient stop elements (`sky1`, `sky2`, `m1a`, `m1b`, etc.) and element IDs (`#sun`, `#birds`, `#bamboo`, `#grass`). `applyPalette()` directly sets `stop-color` attributes and `fill`/`stroke` attributes on these elements to re-theme the illustration per flavor.

### External CDN dependencies

- **Tailwind CSS** (utility classes for some layout)
- **Font Awesome 6.6.0** (icons)
- **Google Fonts**: Inter + Noto Serif SC (for Chinese characters in SVG)
