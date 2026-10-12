# Technical clarification email draft
EXPLORATORY AUTHOR REVIEW — NOT FORMAL STAGE 7

**Draft only. Not sent; no provider contacted.**

To: CDC/ATSDR Environmental Justice Index technical team (contact address to be confirmed)
Subject: EJI 2024 Climate Burden Module: archived zero/null flags and heat interpolation identifiers

Dear EJI Technical Team,

We are auditing the standalone Climate Burden Module in the archived EJI2024 national and California CSV releases for tract-level research in Los Angeles. We use the official RPL_CBM, not RPL_EJI_CBM. Our sources are the EJI2024 CSV archives and EJI_DATADICTIONARY_2024, together with [EJI2024 Technical Documentation](https://atsdr.cdc.gov/place-health/media/pdfs/2024/10/EJI_2024_Technical_Documentation.pdf) and the [Climate Burden indicator descriptions](https://www.atsdr.cdc.gov/place-health/php/eji/eji-indicators-climate-burden-module.html).

Could you please clarify:
1. Are F_NEHD, F_SMOKE and F_BURN available for this exact2024 release, and what are their code definitions? They are absent from the full CSV archives, matching dictionary and raw service we examined.
2. Can E_BURN=0 arise both from no qualifying2013-2022 MTBS wildfire intersection and from source-null/excluded records? Is there an archived field or auditable record distinguishing these cases?
3. Can original zero-versus-source-null/exclusion flags be provided for the archived2024 CBM, including the three fields above? We are not treating all unflagged zeros as missing.
4. Can you provide the GEOIDs, or an auditable identification method, for the13 nationally interpolated extreme-heat tracts described in the technical documentation?
5. For E_HRCN/EPL_HRCN and F_HRCN=1, can geographic source exclusions be distinguished from other source-null conditions? How do zero substitution and FEMA minimum annual-frequency assumptions interact for supported versus excluded tracts?

We retain the published rankings unchanged and would like to report their data-quality limitations accurately. We can supply our archive SHA256s and affected GEOIDs if helpful.

Thank you for your assistance.
Yinchen Yi and Yutong Li
