# Local Path B Elsevier review

This package was initially completed as a local-only export at ecf431ce9487fcfd822e36259f56d61dfec4f180 on review/stage7-path-b-p2-figure7-20261013. The author's subsequent instruction on 2026-10-14 explicitly authorizes committing and pushing the completed review package. Delivery remains on that isolated review branch: no merge, formal Figure 7/S8 replacement, manuscript edit, model refit or physical simulation is performed. Historical pre-delivery QA files retain their original scope and timestamps; the delivery receipt records the subsequent Git/LFS checks.

## Delivered candidates

- FIG07_P2_K3_B_COLOR_NO_REVIEW_BANNER.pdf: preferred full-color candidate, 7.2 x 9.0 inches. Only the archived proof's top review banner was removed in this new copy.
- FIG07_P2_K3_A_TEXTURE_NO_REVIEW_BANNER.pdf: retained texture alternative with identical scientific content to its archived proof.
- FIG07_ACCESSIBILITY_SEPARATE_GRAYSCALE_MAPS.pdf: unnumbered companion with separate, aligned maps of continuous burden and frozen SOVI quartiles. This avoids relying on hue to distinguish quartiles; it is not a combined risk score.
- PART_V_Figure_Structure_Checked.docx and Path_B_Figure_Captions_Checked.docx: checked local copies of the supplied reference documents, preserving their design and current Main 1-7/Supplement 1-10 numbering.

All three figure PDFs are vector artwork with embedded Arial fonts. A/B have 7.5-pt minimum text, no raster images and no page-bound violations. Their minimum positive stroke is approximately 0.10 pt. Font, vector and pixel tests require exact source hashes and exact scientific content outside the removed banner; changed pixels outside that region are zero. Corresponding PNGs are exported at 600 dpi. The contact sheet contains native-color, grayscale and three severity100 color-vision simulations; it is an overview, not a substitute for native-size inspection.

## Scientific and wording checks

The cohort is unchanged: 2,299 positive-population tracts, eight zero-housing tracts included, sixteen zero-population tracts displayed N/A, and 9,066,522 frozen residents. P2/K3 counts remain 1,235/428/636; P2/K4 remains 37/1,217/429/616. All seven P2 coordinates and registered squared-distance budgets are retained. The original five-policy burden identity and frozen Q4/P75 intersection reproduce 94 tracts and 350,799 residents at 38.38135467381475 equivalent hours. The 1,000 realization IDs and physical hashes were read from the compact frozen archive, not fabricated or regenerated.

The new caption document corrects S4C from a supposed separate realization range to the displayed empirical validation distribution and mean. S5 specifies the unchanged 0.50 threshold for the source-only control. The structure table calls Unconstrained a common reference, avoiding the false implication of independent physical samples. The Figure 7 caption makes the common burden-to-lightness mapping across quartile hues explicit. Figure 4/5 realization ranges remain distinct from Figure 6 mean-effect bootstrap confidence intervals. These changes affect only the new local DOCX copies.

## Document rendering

Both DOCX copies render to two pages each. Every final page was inspected for table edges, repeated headers, cell wrapping, page breaks, caption numbering and footer space. No clipping or overflow was found. The supplied landscape structure-table and portrait caption-file layouts are preserved.

LibreOffice is not installed, so the bundled render_docx.py conversion failed. Microsoft Word COM activation/render did not complete; only the exact task-created invisible Word process and its blocked helper were stopped after timeout. WPS native DOCX-compatible read-only export then succeeded, and its PDFs were rendered to PNGs with PyMuPDF. This is real visual QA but not certification that Microsoft Word or publisher production will paginate identically. The later WPS run completed with its automation instance closed.

## Remaining publication conditions

B still loses quartile identity in grayscale and some color-vision simulations. A's hatching also becomes crowded or unresolved in small tract polygons. The separate grayscale companion is easier to read as two independent variables, although the smallest tracts remain small at regional scale. Neither the color map nor the hatch version is universally accessible.

Thin tract boundaries meet the 0.10-pt minimum but many are below the recommended ordinary 0.25-pt weight. They were not indiscriminately thickened, which would change the approved regional maps and obscure small polygons. Printed reproduction of these fine lines remains a production risk. The 7.2 x 9.0-inch size is a working size, not a verified journal maximum or an allowance for same-page captions. Separate caption files are supplied; the journal's submission item/placement rules and final page dimensions still require confirmation.

Official sources consulted 2026-10-14:

- https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-faq
- https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-sizing
- https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-overview
- https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-formats-checklist

Technical export checks are satisfied; journal-specific acceptance and universal accessibility are not certified. Source/protection and file hashes are recorded separately. The active 17 numbered artwork pairs/mirrors, original Git index and 950 protected scientific files remain unchanged. All deliverables are local, untracked outputs in this directory.

## Combined packet synchronized

ALL_FIGURES_WITH_CAPTIONS.pdf now presents all 17 numbered figures with the checked concise captions, followed by the four preserved complementary-evidence pages: 21 pages total. Figure 7 uses the clean B color candidate. Local S8 uses the saved seven-variable P2 diagnostics, with K3 primary, K4 sensitivity and the stronger K4 held-out geographic agreement disclosed. It does not reuse the official eight-variable S8 under a seven-variable caption. The other 15 numbered artwork sources remain unchanged.

The packet builder reads the checked caption DOCX and actual artwork files. QA verifies all caption text, native-scale artwork render identity, the four evidence-page identities, saved P2 memberships, and independent full-cohort silhouette reconstruction. Publication-size renders were inspected without clipping or caption overlap. The updated packet remains a local review output; the tracked official packet, artwork, scientific products and manuscript are untouched. Page hashes and the deterministic rebuild record are provided alongside the packet.
