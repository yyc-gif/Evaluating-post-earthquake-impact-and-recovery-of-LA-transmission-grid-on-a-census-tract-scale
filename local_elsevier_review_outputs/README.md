# Local Elsevier Path B review outputs

Start with FINAL_LOCAL_REVIEW_REPORT.md. The two clean Figure 7 PDFs, separate grayscale-map companion and two checked DOCX copies are the user-facing deliverables. Their 600-dpi PNGs and previews/ contain publication-size/color-vision checks. qa_checked/ contains the final document render proofs; earlier qa/ and qa_final/ render attempts are retained as internal QA, not submission files.

inputs/ preserves exact bytes from Path_B_Local_Elsevier_Review_Package.zip. The ZIP and archived repository proofs are unchanged. The attached preflight source is retained, not overwritten. Local adaptation uses extended Windows paths and treats zero banners as the required clean-export condition, while source inputs still require one banner.

Reproduction uses the existing Python 3.12 analysis environment for build_local_review.py; the bundled dependency Python is used for prepare_review_documents.py. Rendering uses render_review_documents.ps1 -Engine WPS with a new render subdirectory, followed by render_document_pages.py. Export routines refuse to replace earlier PDFs. The initial prepare command freezes preservation and must not be rerun over an existing local package.

The initial export was local-only. On 2026-10-14 the author explicitly requested commit/push delivery, superseding that delivery restriction. This package is delivered on the isolated review branch, without merge or formal promotion. Do not copy its proposed P2 Figure 7/S8 captions into the active eight-coordinate suite piecemeal. FILE_SHA256_MANIFEST.csv records retained review-package bytes; the original PRESERVATION_AFTER.json records the pre-delivery checks, not a claim that this later delivery never occurred.

## Updated combined packet

ALL_FIGURES_WITH_CAPTIONS.pdf is the synchronized local review packet: 17 numbered figures with concise captions on the artwork pages, followed by the four retained evidence pages (21 pages total). It uses clean Figure 7 candidate B and FigS08_P2_K3_K4_Saved_Diagnostics.pdf from frozen P2 results. All other 15 artwork sources are unchanged. Captions come directly from Path_B_Figure_Captions_Checked.docx. This does not replace the tracked official packet or promote the proposed P2 typology.

Run `python local_elsevier_review_outputs/build_all_figures_with_captions.py` in the existing Python 3.12 analysis environment. No models are fitted. Saved silhouette arrays are independently checked against the frozen weighted matrix and labels. ALL_FIGURES_LOCAL_PAGE_REGISTRY.csv and ALL_FIGURES_PACKET_QA.json bind each page to actual source bytes and checked caption text. Rerunning verifies deterministic PDF/PNG bytes. Publication-size reviews are under packet_previews/.

## Git delivery

`verify_git_delivery.py prepare` checks the original protected inputs and source hashes and refreshes the review-package manifest before a scoped commit. After push, `verify_git_delivery.py remote` downloads actual LFS objects into a fresh empty store and records their byte hashes. `remote --no-write` rechecks the final remote HEAD without changing the committed receipts. The older `build_local_review.py verify` is the historical pre-delivery check and intentionally requires the original HEAD/index; use the delivery verifier after committing. Ignored earlier render attempts remain on disk but are not part of the delivered package. No manuscript or formal Stage 7 is changed.
