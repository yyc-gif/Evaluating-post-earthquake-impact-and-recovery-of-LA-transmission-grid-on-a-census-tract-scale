# Author clarity and missing-control correction

Source: `review/official-figure7-candidateA-approved-20261013`, commit
`3c7899f0f328d37b99d2b022f1650c5288a4a664`. This reconciles the newer approved
Candidate A artwork and previously incorporated S10/S11 caption correction,
rather than returning to the older 8f2dcb3 suite.

Implementation branch: `review/figure-suite-author-clarity-numbering-20261013`.
No merge or force-push is performed.

## Implemented

- Continuous supplementary numbering S01-S10. Former S03-S11 move down one
  position; former S02 remains integrated into S01. Main figures stay 01-07.
- Figure 1: meaningful T80 definition, consistent Stage 5 label sizes, explicit
  service-loss gap, frozen quartile sequence and absolute Q4-Q1 gap, no redundant
  Schematic label, and the requested high-vulnerability/slow-recovery hotspot
  direction. The numerical Figure 7 hotspot rule remains pending the next
  author instruction; Figure 7 itself is untouched.
- Current S04: plain GA wording, evaluated repair orders versus physical samples,
  20 individual initial/final run outcomes, independent validation, mean-only
  annotation and named service-loss components. The source search is not rerun.
- Current S05: the previously missing independent source-only control is now
  calculated at threshold 0.50 using the frozen per-realization station integrals.
  Mapping, source connectivity and threshold effects have separate panels.
- Current S09: cool population colors, with original data, log normalization,
  geography and priorities preserved.
- Current captions, manifest, figure index, palette numbering metadata, gallery,
  mirrors, previews and three packets are synchronized. Seventeen numbered
  figures and 38 complete packet pages remain.

## Deliberately unchanged

Figure 7 awaits the author's separate prompt. Formal Stage 7, model inputs,
simulation outputs, frozen vulnerability groups, manuscript, prior reviews and
the original staged/index state are untouched. Thirteen unrelated numbered
PDF/PNG pairs, including Figure 7 and former S09/S11, retain their source bytes.

Former S09 C can support a concise robustness disclosure, not external physical
validation. D exposes class ambiguity but does not need a large standalone
publication panel. Former S11 and Figure 6 are related summaries of the same
resource experiments; retain it only for a distinct absolute-burden question,
otherwise prefer a concise numerical table. These are explicit content
recommendations, not unapproved deletions or replacements.

## Verification

29 figure-suite tests pass, retaining all 26 prior test functions. Independent
tract-based reconstruction covers 3,000 source-control rows; maximum error is
2.85e-14 h. Threshold plots remain pixel-identical in their aligned axes region.
All actual packet figure pages match the actual individual artwork. Original
four evidence pages, all 950 protected files and the source worktree/index are
preserved. Build replay checks all 96 production outputs byte-for-byte.

Exact packet/output hashes, test results and remote real-payload delivery are
recorded in the adjacent JSON files. No new clustering, damage sampling,
restoration scheduling, GA search or service trajectory is generated.
