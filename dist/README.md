# Envelope block

Copy `envelope.html`, `envelope.css`, `envelope.js` and `assets/` together.
Insert the HTML fragment into the page and adjust its relative stylesheet,
script and image URLs if the page lives in another directory. CSS image URLs
are relative to `envelope.css`. No build tools are needed on the host site.
GSAP 3.12.5 loads from cdnjs; Google Fonts provides PT Serif and Montserrat.
Both services need network access. If the host inserts HTML using `innerHTML`,
load the scripts separately and call `EnvelopeSeal.initAll()` afterward.

Set `data-trigger="load|inview|click"` on `.envelope`. Default: inview, once.
Replay is explicit, not a loop. Reduced motion immediately seeks to the final
frame. Each instance has its own timeline and scoped selectors.

API: `element.envelope.play()`, `.final()`, `.timeline`, `.fit()`, `.destroy()`.
The handwritten plans are a fixed raster image, with matching accessible text.
Desktop uses 1280×691 coordinates; mobile uses a 390×700 composition.

Development: `python tools/build_assets_v2.py`, `python tools/build_demo.py`,
then `python tools/frames.py`. `index.html` is generated from this fragment.
QA images and measurements are in `qa/`. Reference-diff thresholds are reported
honestly; regenerated artwork is not pixel-identical to the original reference.

Current review: background quality is being corrected following customer
feedback. Do not treat previous QA functional success as visual acceptance.
