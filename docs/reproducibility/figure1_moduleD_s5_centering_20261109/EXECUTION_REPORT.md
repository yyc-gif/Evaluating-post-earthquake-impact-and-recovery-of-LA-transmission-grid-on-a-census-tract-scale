# Figure 1 Module D and Supplementary Figure S5

## Build authority

The active review-suite branch was `review/s6-main4-20261107` at `5f8e2dec03bc0f94952f6626520f1e0b59c3ae44`. The implementation branch starts from its child centering proposal `5e10f48bbc2b8dc873cc9bda4ad575f8d683cd41`; the proposal changed source logic but had not regenerated these delivered figures. The canonical output generator is `src/la_grid/plotting/build_s6_main4_review.py`.

## Changes

Figure 1 Module D is now a method schematic rather than a numerical recovery-result panel. It distinguishes the Unconstrained parallel-repair reference from priority/GA planning and constrained execution. Its exact new labels are: “Unconstrained reference”; “Repairs proceed in parallel”; “No crew or travel limits”; “Priority rules and GA search”; “Fixed priorities include Vulnerability-first”; “GA search uses service-burden objective”; “Finite crews schedule DS-specific tasks”; “Repair durations vary by damage state”; “Directed road travel links tasks”; and “Schedules set repair-completion times.” The completion sequence shows repair completion, raw station functionality set to 1, source-connectivity reevaluation, and tract service update through `W`. Actual recovery outcomes remain in results figures.

Supplementary Figure S5 is regenerated through `build_s6_main4_review.py`. Its three panels include Impact-first, Hospital-first, Degree-first, and Vulnerability-first. The centering calculation covers the complete visible composition, including strategy labels, titles, axes, ticks, error bars, and legends. The registered scientific values, axes, policy definitions, empirical 5th–95th percentile ranges, colors, and 185 × 210 mm page size are unchanged.

## S5 layout measurements

The 600-dpi delivered raster is 4,371 x 4,961 pixels. Using RGB values below 248 as visible ink, measured margins are 21.289 mm left, 21.120 mm right, 16.847 mm top, and 6.434 mm bottom. The horizontal difference is 0.169 mm. The generator's full text-and-artist bounds independently report 21.186 mm on each side. The three panels remain vertically stacked; no panel, label, or uncertainty interval is clipped.

## Integrity

The S5 plot-data JSON is structurally identical to the starting-branch data. Its starting serialization did not match the SHA recorded in the paired archive audit; the already saved, audit-matching serialization was restored. Parsed values are identical to the starting branch, and the final data SHA matches the audit record. The final PDF renders byte-identically to the delivered 600-dpi PNG encoding, and the 150-dpi preview also matches a PDF render. In the complete packet, the S5 artwork region matches the standalone PDF raster pixel-for-pixel. The figure manifest and PDF/PNG mirrors are synchronized. Only Figure 1 and S5 PDF/PNG artwork pairs differ from the starting implementation commit; remaining numbered artwork is retained byte-identically.

No simulation, damage realization, recovery trajectory, repair schedule, or scientific result was rerun. The original source figure suite is read-only; the separate review suite is the only generated target.

## Verification

The active promotion integration test file passes all 13 tests. Two canonical builds produced identical SHA-256 values for all 103 files under the review suite and its mirror. The four modified artwork files are Figure 1 PDF/PNG and S5 PDF/PNG; the other 28 numbered artwork files match their starting-commit LFS object hashes. Figure 1's non-Module-D rendered pixels are identical to the source at 120 dpi. The 8-main/8-supplement collection remains a 16-page complete figure-and-caption packet.
