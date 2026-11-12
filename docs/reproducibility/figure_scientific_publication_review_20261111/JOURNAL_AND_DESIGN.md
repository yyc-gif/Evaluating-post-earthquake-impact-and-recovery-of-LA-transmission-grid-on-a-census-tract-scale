# Journal gate and unified artwork system

## Journal identity and verified requirements

The working submission evidence favors **International Journal of Disaster Risk Reduction (IJDRR), Elsevier**: the available manuscript is named `Manuscript_IJDRR.docx`, the workflow export name is IJDRR, and recent author instructions explicitly name IJDRR. However, an older `figure_layout_preflight_20261108/LOCAL_EXECUTION_BRIEF.md` calls IJDRS the selected journal. The manuscript body contains no definitive submission declaration. Treat IJDRR as the working target, with final journal confirmation still open; do not conflate the journals.

Checked on 2026-11-11:

- [Elsevier official artwork sizing](https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-sizing): approximately 7 pt normal lettering is a rule of thumb, not an absolute journal rule; keys and symbols must remain discernible. General target widths are 90, 140 and 190 mm. Bitmap guidance distinguishes 300 dpi halftones, 500 dpi combination art and 1000 dpi line art. Vector PDF masters are retained; 600-dpi PNGs are sharing/review previews, not a claim that pure raster line-art requirements are met.
- [IJDRR live Guide for Authors](https://www.sciencedirect.com/journal/international-journal-of-disaster-risk-reduction/publish/guide-for-authors): returned HTTP 403. Journal-specific figure-count/height limits, file rules and color/submission constraints could not be confirmed. No strict numerical margin or panel-gap rule is inferred.
- [IJDRS official submission page](https://link.springer.com/journal/13753/submission-guidelines) links [Instructions for Authors](https://media.springer.com/full/springer-instructions-for-authors-assets/pdf/1687518_174131257_IFA_13753.pdf). The linked document permits up to five figures and three tables without special editorial permission, requests separate high-resolution TIFF/JPEG at least 300 dpi and defined abbreviations. The current eight-main-figure collection therefore cannot be certified for IJDRS without permission or reorganization. That served document does not establish the often-cited generic Springer 234-mm height rule for this journal.

If IJDRS is selected, an evidence-preserving five-main option is workflow, damage/service, source connectivity, strategy outcomes and distributional effects (current 1/3/4/5/6), with mapping validation, resource effects and descriptive typology moved to supplementary material. This is a recommendation only: no numbering or scientific panels are deleted or moved in this revision.

The actual served IJDRS instruction PDF has SHA256 `b05e9c4d16cc863425f1340962a4e89ffcb509e51765224ec61863bb597c6ea3`. Any reduction from the native figure width must be rechecked: reducing 185 to 174 mm would turn 7-pt lettering into about 6.6 pt. This is a size-sensitivity calculation, not a claim that IJDRS requires 174 mm.

## Final design system

- Arial throughout; charcoal headings, consistent regular/bold hierarchy. Main statistical text generally 7-9.5 pt at native width; Stage 4 minimum 7.5 pt. Actual extracted sizes and measured ink margins are recorded separately, not substituted for visual review.
- Teal encodes repair/activity or the workflow's state example; gray is travel. Strategy colors retain their established identities across outcome and resource figures. Cluster colors remain categorical and separate from the continuous blue-amber bivariate scale.
- Absolute levels, paired changes, cumulative deficits, T80 and network-only reliability use explicit distinct labels and units. Realization percentiles and mean-effect bootstrap intervals are separately identified.
- White background; thin restrained axes/rules; existing meaningful color scales and map projections preserved. No invented geographies or arbitrary state icons. Stage 4 uses actual archived states, not new simulation output.
- Geographical and statistical panels retain suitable aspect ratios rather than being forced into identical boxes. Figure 1 retains the five-stage flow and full-width three-column Stage 4.
- Individual PDF and 600-dpi PNG art exclude captions; captions remain separately supplied and also appear in the review packet. The packet is not itself a journal upload template.

## Remaining accessibility and submission limitations

The continuous bivariate community map cannot encode both variables independently in grayscale. Its existing aligned single-variable accessibility references remain relevant; color submission and accompanying accessible description must be confirmed. Dense small-tract maps need the vector master or enlarged supplementary view. The palette is not certified universally color-vision safe simply because it is muted.

The preserved single-variable companion is `results/diagnostics/1021/figure7_readability_20261015/FIG07_ACCESSIBILITY_ALIGNED_SEPARATE_MAPS.pdf`; it is not given another numbered figure slot or duplicated into the publication packet.

Elsevier's [artwork FAQ](https://www.elsevier.com/en-in/about/policies-and-standards/author/artwork-and-media-instructions/artwork-faq) recommends small upload files (generally below 10 MB, and below 7 MB when several are supplied); it also says journal limits can differ. The vector masters for Figure 1 (about 36.1 MiB) and S1 (about 11.5 MiB) exceed that general recommendation. No journal-specific rejection threshold was verified. They have not been rasterized or stripped of source content to make an unsupported compliance claim; confirm the actual submission portal's limits before uploading. Review packets and 600-dpi sharing PNGs are not substitutes for separate production artwork.

No new empirical outage validation, proof of discrete cluster structure, capacity-flow validation, significant hotspot test or optimal intervention ranking is established by these artwork changes. Journal-specific acceptance and current manuscript alignment remain author/editorial gates.
