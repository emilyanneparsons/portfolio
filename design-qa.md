# Design QA

## Evidence

- Approved visual direction: `assets/homepage-hero.png` (desktop) and
  `assets/homepage-hero-mobile.png` (mobile).
- Approved sailboat direction: `assets/sailboat-red-sloop-source.png`, the
  user's selected Option 1 (1254 × 1254 source pixels).
- Final sailboat implementation: `qa-boat-route-standard-turn.png`
  (1800 × 897 pixels at an 1800 × 897 CSS viewport and 1× capture density).
- Combined full-view and focused comparison:
  `qa-boat-route-comparison.png` (1500 × 1160 pixels). It includes the concealed
  entrance plus turnaround states at standard, short/wide, and tall desktops.
- Ambient-motion comparison: `qa-ambient-animation-comparison.png`, showing two
  staggered desktop frames with all six seagulls and the Ferry Building flag.
- Ambient responsive captures: `qa-ambient-wide.png` at 1920 × 700 and
  `qa-ambient-mobile.png` at 390 × 844.
- Refined motion comparison: `qa-refined-motion-comparison.png`, combining the
  user's reported mid-bush sail reveal, the corrected concealed/edge-emergence
  states, and two frames of the stronger gull wingbeat.
- Final unclipped boat states: `qa-boat-visible-start-v4.png` at page load and
  `qa-boat-moving-v4.png` after 2.5 seconds of continuous motion.
- Focused before/after evidence: `qa-unclipped-boat-comparison.png`, showing the
  reported sliced return beside the intact load and moving states.
- Responsive captures: `qa-homepage-wide.png`, `qa-homepage-standard.png`,
  `qa-homepage-tall.png`, `qa-homepage-mobile.png`, and
  `qa-homepage-chrome.png`. The final desktop cloud adjustment is captured in
  `qa-homepage-chrome-clouds.png`.
- Side-by-side reviews: `qa-comparison-standard.png` and
  `qa-comparison-mobile.png`. The reported Chrome collision and final fix were
  reviewed together in `qa-comparison-chrome-fix.png`. The reported desktop
  cloud crop and adjusted composition were reviewed together in
  `qa-comparison-desktop-clouds.png`.
- Viewports tested: 1920 × 700, 1800 × 897, 1595 × 1357, 1440 × 900,
  1280 × 1024, and 390 × 844 CSS pixels, plus the user's actual 1800 × 896
  Chrome content viewport at 2× device-pixel ratio.
- State: homepage hero with the cloud-title animation running.

## Findings

- No actionable P0, P1, or P2 differences.
- The sky and skyline fill every tested viewport edge to edge. The background
  bounds matched the viewport bounds and no flat-color padding was visible.
- The cloud title is positioned independently from the background and centered
  within the open-sky region. It remained fully visible at every tested size.
- The title is constrained to the upper half of normal desktop layouts. An
  additional wide-and-short breakpoint reserves an even smaller safe sky zone
  above the skyline.
- In the user's Chrome viewport, the title's lower bound remained above the
  Transamerica Pyramid throughout the sampled float cycle.
- The desktop title cap was increased by approximately ten percent after the
  skyline-safe placement was established.
- The two large desktop edge clouds were moved farther down in a new background
  asset so their full silhouettes remain visible in the user's wide Chrome
  viewport. The center sky stays open for the title.
- The title scales down for portrait screens while preserving the two-line name
  treatment and visual hierarchy.
- The implementation retains the approved paper-cut color, texture, landmarks,
  and cloud-lettering style.
- The six animated gulls and Ferry Building flag use transparent cutouts from
  the approved desktop artwork, so their paper texture, shadows, scale, and
  original positions remain visually consistent with the skyline.
- The Ferry Building mast is restored as a separate static paper cutout beneath
  the animated flag. Its white structure no longer blends into the blue sky.
- The new boat preserves the selected source's warm red hull, cream paper
  sails, tan mast, tactile texture, and soft dimensional shadow. Its transparent
  cutout has no visible blue box or masking halo against the homepage.
- At desktop sizes, the boat remains a secondary ambient detail beneath the
  Golden Gate Bridge and does not compete with or overlap the name. It is
  layered in front of the skyline and behind a transparent foreground foliage
  cutout made from the exact background pixels.
- The only visible copy is “EMILY PARSONS.” A visually hidden semantic heading
  preserves the page structure for assistive technology.

## Required Fidelity Surfaces

- Fonts and typography: unchanged; the sailboat adds no text and the approved
  cloud-letter title retains its existing size, weight, wrapping, and hierarchy.
- Spacing and layout rhythm: the boat's world layer uses the background's exact
  1486:1058 aspect ratio and the same centered, bottom-anchored cover geometry.
  At 1800 × 897 its rendered bounds are approximately 58 × 59 pixels, keeping
  it distinctly smaller than the Golden Gate Bridge.
- Colors and visual tokens: red-orange, cream, tan, and navy tones align with
  the existing Golden Gate Bridge, architecture, and paper-cut palette.
- Image quality and asset fidelity: the generated bitmap is used directly as a
  transparent lossless WebP; edges, rigging, paper texture, and shadows remain
  legible at display size with no CSS or SVG approximation.
- Copy and content: unchanged; no new visible copy was introduced.

## Motion and Browser Checks

- The cloud title uses a slow seven-second ease-in-out float with a subtle
  two-tenths-degree rotation.
- On the 1920 × 700 stress test, the visible cloud letters remained above the
  skyline and fully on-screen.
- Reduced-motion preferences disable the animation.
- The boat is fully visible at 23% of the shared scene width on page load, then
  immediately follows a slow 32-second back-and-forth cruise over another 14%,
  preserving the same 37% turnaround point just past the Ferry Building
  midpoint. A separate 3.6-second, three-pixel bob adds water motion. No boat
  ancestor uses `clip-path`, so the hull and sails remain intact at both ends of
  the route. Direction flips occur over 0.2% of the cycle so the boat does not
  visibly compress during the turn.
- Reduced-motion preferences stop the boat's cruise and bob, leaving it fully
  visible in a stable desktop position.
- The six gulls flap in place on staggered 1.08–1.22 second beats. Their
  horizontal and vertical coordinates remain fixed; only a subtle vertical
  silhouette compression and fractional rotation create the wingbeat. The
  closed-wing frame now reaches 46% of the open silhouette height so the motion
  reads more clearly while retaining the original tempo.
- The Ferry Building flag ripples on a gentle 1.8-second cycle and remains
  anchored to the original tower-top position.
- Reduced-motion preferences stop both new ambient animation groups.
- Mobile remains on `assets/homepage-background-mobile.webp`; its 390 × 844
  title bounds remained identical to the previously approved capture, and the
  desktop-only ambient, bay, and foreground layers computed to `display: none`.
- Document dimensions matched the viewport at all four sizes; no horizontal or
  vertical overflow was detected.
- Console errors and warnings: none.
- Primary interactions tested: none; this homepage intentionally contains no
  controls.

## Comparison History

- The first responsive pass used `object-fit: contain`, which exposed a flat
  blue surround on some desktop aspect ratios.
- The background was changed to a full-bleed, bottom-anchored cover treatment.
- The animated title was separated into its own transparent layer and placed in
  a dedicated sky stage so background cropping cannot push the name off-screen.
- A Chrome-specific visual report exposed that the original desktop title cap
  was still too large. The safe sky zone and title caps were tightened, with a
  separate rule for desktop windows wider than 9:4.
- A later desktop-only polish pass introduced
  `assets/homepage-background-desktop-v2.webp`, lowered the two upper edge
  clouds, and slightly enlarged the title. The portrait asset and mobile sizing
  were intentionally left unchanged.
- Final side-by-side review confirms that the updated composition preserves the
  approved direction while preventing both top clipping and skyline overlap
  across the tested sizes.
- The first boat placement settled near x=108 at 1800 × 897 and read as sitting
  on top of the far-left foreground bush. The desktop endpoint was moved to
  x=198 and the cruise range tightened to 12vw, placing the boat beneath the
  bridge in the intended bay pocket. The final full-view and focused comparison
  shows the corrected entrance/cruise region with no remaining P0/P1/P2 issue.
- User review then identified two P2 depth/scale issues: the 108-pixel boat read
  too close to the bridge's height, and the single-layer composition made it
  appear to float on top of the scenery. The boat cap was reduced to 58 pixels,
  its cruise region was extended in front of the Ferry Building, and
  `assets/homepage-foreground-bushes.webp` was added above the boat. Post-fix
  evidence in `qa-sailboat-layering-comparison.png` shows the boat concealed by
  the foliage on entry, then visible in front of the Ferry Building. The cruise
  sample moved 173 CSS pixels over 3.5 seconds with no jump or pause.
- A later review exposed that viewport-based bottom and horizontal offsets could
  lift the boat out of the water on tall desktops and let it overlap the
  right-side greenery. The route was moved into a world layer that matches the
  background's exact cover scaling, anchored 1% above the artwork's bottom.
  Its start was moved deeper behind the left bushes and its cruise distance was
  reduced from 30% to 25%. `qa-boat-route-comparison.png` verifies the full
  entrance and turnaround at 1800 × 897, 1920 × 700, and 1595 × 1357: the boat
  stays in the water, begins under the bridge behind foliage, and reverses
  before the right greenery. No console errors or viewport overflow occurred.
- For the bird and flag animation pass, the desktop background was cleaned only
  at the original six bird silhouettes and tiny flag area, then the exact
  raster details were restored as independent transparent layers. The final
  background differs from the approved desktop artwork at only 4,507 of
  1,572,188 pixels (0.2867%), preserving the skyline and paper sky. Tall and
  wide desktop captures confirm the layers track the same 1486:1058 cover
  geometry as the background, while the mobile capture remains unchanged.
- User review exposed a P2 depth issue in the entrance: the foreground pixels
  covered the hull, but the tall sail became visible through a lower part of the
  bush silhouette. The bay layer now clips the boat through 23% of the shared
  scene width. At 1.6 seconds the measured visible boat width is zero at
  1800 × 897, 1920 × 700, and 1595 × 1357; near the end of the entrance it
  appears progressively from the bush's right edge. The endpoint remains 37%,
  so the right-side turnaround is unchanged. The same pass increased the gull
  flap amplitude and restored the exact white tower-top mast beneath the flag.
- A later user review exposed a second P2 issue caused by that reveal boundary:
  the persistent scene-space clip could slice the boat vertically when it
  returned to the left. The final implementation removes clipping and the
  one-time concealed entrance entirely. The boat now starts fully visible at
  23%, cruises from 23–37%, and never travels into the former hidden zone.
  `qa-boat-visible-start-v4.png` shows the intact load state, while
  `qa-boat-moving-v4.png` confirms motion begins immediately. At 1440 × 900 the
  boat moved 11.8 CSS pixels in the first 2.5 seconds; both its entry and bay
  layers computed to `clip-path: none`.

## Focused Comparison

- A focused comparison was necessary because the sailboat is roughly three percent of
  the desktop width. The layered states in `qa-boat-route-comparison.png`
  confirm the selected silhouette, materials, and proportions remain clear in
  context while the transparent edge blends into the scene. The entrance and
  ferry-pass frames also verify the intended foreground/midground/background
  ordering.
- Residual P3 note: the boat intentionally uses its own soft shadow rather than
  matching every baked shadow angle in the skyline; at its ambient scale this
  difference is not noticeable in the full view.

final result: passed
