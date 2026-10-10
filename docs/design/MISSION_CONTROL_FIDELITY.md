# Mission Control fidelity and full-site delivery

## Outcome

The visual recovery implementation passes the functional/layout gate. It is a reference-guided prototype, not a pixel-identical reproduction or operational astronaut navigation certification. Latest scope includes landing, Mission Control's five local workflow contexts, Astronaut View, Evidence Inspector, Exploration Memory and Before & After.

## Desktop geometry

Measured at CSS 1440 x 900: rail 52 px, header 56 px, local workflow 40 px, left column 240 px, right column 294 px, 8 px gaps, map column 822 px. Map workspace begins at y=104 and is 684 px tall; timeline is 104 px. Map column occupies 43.4% of the viewport. Side inspectors scroll internally when needed. Global navigation stays in the utility rail; tabs change context without leaving `/mission`.

## Semantics and behavior

- Entire Alpha remains an off-white prior route. A separate amber dashed overlay marks only canonical affected segment 3; rejected, superseded and expired evidence cannot create an active challenge.
- Confirmed Beta reveals progressively. Reduced-motion users receive immediate routes and no decorative motion.
- Area 14, habitat, target and astronaut markers retain canonical local geometry. Astronaut shares the seeded habitat position; no fabricated movement or camera coordinates.
- One right inspector responds to EXPECT / OBSERVE / COMPARE / VERIFY / LEARN, evidence or timeline selection.
- Existing confirm / request more evidence / reject guards and API writes remain. Weak terrain still requires explicit human identification. Confirmed footprint knowledge and rerouting survive reload.
- Evidence separates NASA prior, observation, actual model output or curated replay, human interpretation, decision, mission consequence, provenance and history.
- Memory selections highlight supported evidence locations. Future EVA inherits verified local persistent knowledge; dynamic conditions expire.
- Before/after maps use the identical snapshot and locked extent. Slider and buttons change only the comparison split.

## Visual constraints

Real cached HiRISE/CTX provide the map. A disclosed warm presentation tint leaves source bytes/provenance unchanged. Genuine Navcam is used for observation/landing. Frozen geometry produces a mostly horizontal Alpha and a footprint-bounded alternative, unlike the generated diagonal showcase route. No decorative telemetry, invented elevation profile, invented model confidence or region-wide ground truth was added. Fonts use the local system sans stack with compact technical monospace labels; the screenshot contains no available font metadata.

## Validation

70 backend tests and 9 frontend tests passed. ESLint, TypeScript and production Next build passed. A Windows generated-folder permission error on the default build was resolved with an isolated production output directory. Manual in-app-browser acceptance covered analysis, provisional evidence, confirmation, Beta, reload, future inheritance, local keyboard tabs, structured history, spatial selection, slider buttons/keyboard, fullscreen Escape/focus and mobile navigation.

CSS viewport requests: 1440x900, 1280x800, 834x1112, 390x844. Desktop saved PNGs match requested dimensions. The browser capture adapter returned 819x1041 and 375x811 for the tablet/mobile PNGs (scrollbar/chrome/capture limits); these are not represented as exact full-height device captures. DOM checks reported no horizontal overflow. All screenshots are in `../screenshots/visual-recovery/`.

See `../../design-qa.md` for paired visual evidence, iteration history and remaining scientific gaps. Automated Playwright suites were not rerun for this design pass. User runtime data and original services were preserved. No application deployment was performed.
