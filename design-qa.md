# Design QA - full-site visual recovery

**Final result: passed**

This result applies to the requested prototype UI recovery and tested interactions, not scientific source completion or operational safety certification.

## Visual truth and comparison evidence

Source: `C:/Users/ACER/Downloads/MARSENSE_ Mission Control UI Showcase.png`, 1536x1024 pixels. Earlier four original images are audited in `docs/design/REFERENCE_AUDIT.md`. Implementation: `docs/screenshots/visual-recovery/full-system-showcase.png`, 1600x1100 contact sheet of actual browser renders. Both were opened together as `docs/screenshots/visual-recovery/source-render-comparison.png` (1600x2200). Source is uniformly contained into 1600x1067; actual views are uniformly contained in 515x245 tiles. This normalization permits composition comparison, not pixel-difference equivalence. Full-size Mission Control: `docs/screenshots/visual-recovery/mission-1440x900.png` (1440x900, CSS 1440x900). Focused map/panel regions were inspected in full-size browser screenshots; a separate crop was unnecessary.

State: isolated local demo, EVA-01, original prior retained, provisional record confirmed by human, Beta active; VERIFY screenshot intentionally captures the earlier provisional state. Montage includes all ten workflow/screen states. Frozen mission geometry and NASA assets intentionally differ from generated reference artwork.

## Required fidelity surfaces

| Surface | Finding and disposition |
|---|---|
| Typography | System sans and compact monospace labels; uppercase technical hierarchy, clear large target and route values. Source font identity unavailable. Font-family difference is expected; matching local density/hierarchy checked. |
| Spacing/layout | Frozen 52/56/40 px rail/header/tabs, 240/294 px inspectors, 8 px gaps. Map dominates desktop; controls remain reachable; tablet/mobile reorder map first and scroll. Square 1 px panels retained. |
| Color/tokens | Near-black shell, charcoal frames, off-white prior, amber challenge, mint confirmed/Beta. Warm tint is disclosed and presentation-only. Scientific source colors are retained in original observation previews. |
| Assets/quality | Genuine cached NASA raster and Navcam images, original provenance retained. No generated globe, spectral classification or handmade substitutes for NASA imagery. Lower-resolution landing panorama and real orthographic terrain differ from showcase; expected source constraints. |
| Copy/content | Core identity/workflow retained. Placeholder telemetry, AI performance, arrival time and invented elevation removed. Canonical modeled distance and actual history shown. Confirmed evidence does not keep an active provisional warning. |

## P0/P1/P2 iteration history

1. Earlier drift (`anti-reference.png`): duplicated navigation, pushed-down map, overstacked inspector, grayscale imagery, challenged whole Alpha, below-fold timeline. Fixed shell geometry, local tabs, single contextual panel, real warm imagery, separate affected segment overlay, compact spatial timeline. Post-fix: `mission-1440x900.png` and five context captures.
2. First recovery (`mission-first-1440.png`): muted raster, oversized frame margins and left-stack overflow. Fixed raster opacity/tint, mission extent fit, compact trace/labels and internal inspector scrolling. Post-fix: desktop 1440/1280 captures.
3. Mobile stack: block shell left a large gap and map/control geometry overflowed. Fixed rail/content grid, map-first reflow, compact map height, accessible scrolling. Post-fix: `mission-390x844.png`, `mission-834x1112.png`; DOM scroll widths 375/819 do not exceed CSS widths 390/834.
4. Mobile navigation tooltip covered the adjacent icon. Fixed `.nav-label` pointer-events and right-side placement. Evidence navigation verified to `/evidence` after fix.
5. Confirmed Astronaut View continued showing the old provisional alert. Fixed confirmed ground-observed summary and recorded-consequence terminology. Post-fix: `astronaut-1440.png` and reload acceptance.
6. Marker captions offset canonical positions; astronomical coordinate label could imply measured camera placement. Fixed marker anchor offsets and removed the coordinate label. Canonical source geometry remains unchanged.

No actionable P0/P1/P2 visual findings remain in the tested prototype scope. P3: a dedicated licensed display font or higher-resolution source-supported landing panorama could improve polish; no fabricated asset is needed for this gate.

## Validation and gaps

70 backend tests, 9 frontend tests, lint, TypeScript and production build pass. Manual browser checks: provisional analysis -> human confirmation -> Beta -> reload -> future EVA inheritance; arrow-key local tabs; evidence hierarchy/history; spatial event location; Before/Split/After and slider keyboard; fullscreen Escape/focus restoration; mobile rail navigation. Browser logs: no console errors in the final checked screen sequence; one Next development LCP eager-loading advisory for an orbital preview image. Reduced-motion branches are implemented and code-reviewed, not OS-emulated. Upload/reject/request-more paths retain tested existing backend/component guards; they were not all manually replayed in this final UI sequence. Automated Playwright suites were not run for this design pass.

Viewport requests 1440x900 and 1280x800 produce exact PNGs. Tablet/mobile capture output was 819x1041 / 375x811 despite CSS requests 834x1112 / 390x844; report these honestly as adapter-limited captures. Horizontal-overflow DOM checks pass. No claim of exhaustive device testing.

Scientific gaps remain: reliable classifier disabled, camera footprint/georegistration unresolved, CRISM validation gap, slope unavailable, illustrative replay geometry. See FINAL_AUDIT.md and implementation status.

## Implementation checklist

- [x] All ten reference contexts represented across six app destinations.
- [x] Frozen desktop shell, responsive map-first mobile composition.
- [x] Original prior, human decision authority, footprint limits and source provenance preserved.
- [x] Paired reference/render evidence reviewed and reports saved.
- [x] Appropriate backend/component/build/manual acceptance checks.
- [x] README documents setup, workflow, limits, testing and Git/GitHub usage.
- [ ] Operational astronaut validation and unresolved scientific source gates (separate scope).
