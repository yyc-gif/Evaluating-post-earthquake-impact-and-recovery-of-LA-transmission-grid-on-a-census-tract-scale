# Reuse without scientific redesign

Keep stable identities in `universal/MASTERS.json`. A journal's Figure 2 is a configuration label, not a renamed dataset or overwritten scientific master. Resolve numbering through a crosswalk, including references embedded in artwork; never apply a blind global number shift.

| Production request | Practical route | Check before delivery |
|---|---|---|
| Vector PDF | Registry-selected native delivery PDF; full-resource original remains available | Fonts, vector paths, scientific labels and final printed size |
| TIFF, at least 300 dpi | Supplied native 600-dpi LZW RGB files, or the explicit raster exporter | Real file format, effective dimensions, pixel round trip, color interpretation |
| Higher-resolution line art | Explicit `--dpi 1200`, only when requested | Large byte size is not extra scientific detail; printed lettering does not become larger |
| PNG for coauthors | Existing caption-free 600-dpi master counterparts | Avoid a redundant export/upload when source and appearance are unchanged |
| Different column width | Explicit `--width-mm`, with the lettering-size guard | A dense 185-mm figure generally needs reflow rather than single-column shrinking |
| SVG | No approved derivative: the trial failed its appearance gate | Do not deliver a conversion merely because it is vector-only; preserve PDF/code/captions |
| EPS | Requires a suitable converter and fresh visual/font/transparency checks | Not generated or certified by this package |
| JPEG | Only a separately reviewed request for suitable continuous-tone content | Do not JPEG-compress scientific lettering or vector maps merely to reduce bytes |
| CMYK or grayscale production | Publisher-specific proof/conversion | The supplied sRGB TIFF is not a calibrated CMYK proof; the bivariate map loses a variable in grayscale |
| Five, six or eight main figures | Separate editorial configuration with all evidence preserved | Figure limits and supplementary acceptance are journal-specific; author/editor approval remains necessary |

Examples are in the package README and `EXPORT_PROFILES.json`. The exporter changes presentation only. It does not import the scientific simulation, restoration, GA or clustering engines. Captions remain separate from individual artwork; captioned PDF packets are review aids rather than imitations of final typeset pages.
