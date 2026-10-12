# Measurement families: do not substitute one for another

AUTHOR REVIEW - NOT FORMAL STAGE 7

The exact California archive contains 9,106 2020-tract records, all NRI_VER=Mar-23.
The current analysis matches all 2,299 positive frozen-population GEOIDs. No FEMA population replaces formal population.

**H physical exposure:** MS48 probabilistic PGA, CAL FIRE severity classes, NFHL probability-zone area, historical CDC extreme-heat days are distinct source-defined environmental measurements. None is electricity-outage damage.

**L loss propensity:** ALR_NPCTL nationally ranks an EAL-weighted combination of consequence-specific loss-rate percentiles. ALRB/ALRP/ALRA refer to building/population/agriculture rates; missing or zero-exposure denominators are not measured zero loss propensity. These retain modeled frequency and loss-ratio assumptions; they are not intensity or balanced physical exposure. See v1.19 PDF pp93-95 (printed 5-34 to 5-36).

**E expected loss:** EAL_VALT is modeled annual building + monetized population + agriculture loss (2022 USD/year); EAL_SCORE is its national percentile. On this cohort earthquake contributes **98.165356%** of pooled EAL; median within-tract earthquake share is 99.274498%. This updates, rather than inherits, the older residential 98.1563% calculation. Null hazard contributions remain null; the available-component sum matches the published total within 7.45e-09 USD.

**Adjusted risk:** RISK_VALUE=EAL_VALT*CRF_VALUE; CRF embeds SOVI/resilience. RISK_SCORE and ALR_VRA_NPCTL are excluded as primary physical hazard coordinates. Statistical correlation is separate from this procedural dependence.

v1.19 p44 (printed 3-6): Not Applicable, Insufficient Data and No Expected Annual Losses have different meanings. The archive's exact ratings and nulls are retained. A zero EAL can arise from zero exposure or frequency; it is not proof of physical safety. Historical EVNTS can be zero while minimum modeled AFREQ is positive (e.g. landslide). Table 6 (PDF p63) confirms mixed events, event-days and probability supports; raw AFREQs are never summed. EXP_AREA is source-defined exposure geography, not exposed resident population.

Official FEMA v1.19 technical documentation, March 2023, preserved by Ohio Emergency Management: https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf . The exact previously verified PDF and evidence pages are copied, not replaced by a newer technical release.
