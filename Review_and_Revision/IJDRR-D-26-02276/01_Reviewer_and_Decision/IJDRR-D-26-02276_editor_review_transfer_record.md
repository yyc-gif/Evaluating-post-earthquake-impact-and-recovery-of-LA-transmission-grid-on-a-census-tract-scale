# IJDRR-D-26-02276 — Editorial Decision, Reviewer Reports, and Transfer Information

## Purpose and provenance

This file consolidates the editorial and reviewer information received for manuscript **IJDRR-D-26-02276**, together with the journal-transfer information subsequently displayed by Elsevier. It is intended to be placed in the local research-project folder so that a local AI can compare the reviewers’ statements against the manuscript, source code, data, configuration, and generated results.

Source hierarchy:

1. The editorial decision and both reviewer reports below are transcribed from the decision email received on **12 September 2026**. The substantive text is reproduced verbatim; email tracking links, account-removal links, routine customer-support material, and anti-fraud boilerplate are omitted.
2. The transfer-notification text is transcribed from Elsevier’s subsequent email received on the same date.
3. The transfer-journal table is transcribed from the author’s Elsevier Transfer Your Manuscript page. Metrics and charges are a snapshot of what that page displayed on **12 September 2026** and should not be treated as permanent journal data.
4. The final section records procedural facts checked against official Elsevier and University of California pages. It is contextual information, not reviewer commentary.

No transfer has yet been completed. The formal IJDRR decision was a rejection, not an invitation to revise for IJDRR.

## Manuscript identification

- **Manuscript number:** IJDRR-D-26-02276
- **Submitted title:** *Post-Earthquake Power Service Recovery in Los Angeles: Linking Substation Damage, Restoration Logistics, and Tract-Level Disparities*
- **Journal:** *International Journal of Disaster Risk Reduction*
- **Decision date:** 12 September 2026
- **Editor named in the decision:** Vitor Silva, Associate Editor
- **Formal outcome:** Reject, followed by an Elsevier transfer offer

## Editorial decision — substantive text

> Dear Mr. Yi,
>
> Thank you for submitting your article, as listed above, to the International Journal of Disaster Risk Reduction.
>
> To view your reviewer feedback, please log in as an author at https://www.editorialmanager.com/ijdrr/ and navigate to your manuscript in the "Submissions with a Decision" folder under the Author Main Menu.
>
> I regret that I cannot accept your manuscript for publication in this journal.
>
> I hope that you can find a more appropriate outlet elsewhere for your work.
>
> For alternative journals that may be more suitable for your manuscript, please refer to our Journal Finder.
>
> We appreciate you submitting your manuscript to International Journal of Disaster Risk Reduction and thank you for giving us the opportunity to consider your work.
>
> Kind regards,
>
> Vitor Silva  
> Associate Editor  
> International Journal of Disaster Risk Reduction

The decision letter did **not** invite a revision at IJDRR and did **not** name a destination journal. The separate Elsevier transfer service later supplied the journal list.

## Reviewer 1 — complete report

> This manuscript develops a census-tract-level framework for post-earthquake power-service recovery in Los Angeles County by integrating substation damage, network connectivity, restoration logistics, and social vulnerability. The study is relevant to IJDRR and provides a useful attempt to link infrastructure recovery with community-level impacts. However, several key assumptions and the model validation require further clarification to support the robustness of the conclusions.
>
> 1. The census-tract service availability is derived from an IDW-based dependency matrix using tract centroids, network distances, and an assumed cutoff. However, this mapping is not supported by actual utility service territories, feeder connections, or outage records. Since the subsequent population-weighted recovery, hospital prioritization, and vulnerability hotspot results all depend directly on this matrix, the authors should provide stronger validation or robustness analysis for the tract-substation mapping, beyond varying only the weight cutoff. The limitations of interpreting this proxy as actual electricity-service dependency should also be more clearly stated.
>
> 2. The reduced network is explicitly stated not to be an electrical power-flow equivalent, while service availability is determined mainly by whether a substation remains connected to an active source. This ignores power balance, transmission capacity, line loading, generation availability, voltage constraints, and load shedding. The authors should clarify under what conditions source connectivity can reasonably serve as a proxy for electricity availability and avoid interpreting the modeled S_r (t) as equivalent to actual delivered power unless additional validation is provided.
>
> 3. Damage states and restoration durations are generated through Monte Carlo simulation, but the scheduling stage subsequently uses the Monte Carlo mean restoration duration as a representative value for each substation. It is unclear how the scenario-specific repair-task set is determined when damage itself varies across realizations, and how uncertainty in damage and repair duration propagates into the reported strategy rankings.
>
> 4. The comparison with historical restoration records provides a useful contextual check on the overall recovery timescale, but it should not be interpreted as a validation of the tract-level recovery model. In particular, the framework does not explicitly represent distribution feeders, customer-level switching, or utility emergency operations, and discrepancies remain across different recovery milestones. The authors should therefore more clearly frame the model as a scenario-based tool for comparing alternative restoration strategies rather than as a predictive representation of actual post-earthquake power restoration.
>
> 5. The current SVI-weighted recovery measure is essentially a population-and-SVI-weighted average service trajectory. An earlier SVI-weighted T_80 does not necessarily imply a more equitable restoration outcome, nor does it directly quantify inequality among communities. Indeed, the manuscript finds that SVI-weighted T_80 is often slightly earlier than population-weighted T_80. The authors should either introduce more explicit distributional-equity measures—such as recovery gaps between vulnerability groups or inequality measures—or moderate the claims regarding social equity. Similarly, the K-means typologies and top-10 composite hotspot score should be described primarily as descriptive screening tools rather than evidence of causal relationships between social vulnerability and delayed recovery.
>
> 6. The GA formulation requires more information on implementation and reproducibility, including population size, number of generations, crossover/mutation settings, stopping criteria, repeated runs, and convergence. The weighting choices in Table 2, particularly the hospital weight of 20, also require justification.
>
> 7. The manuscript should explain more clearly why the relatively simple Hospital-first rule outperforms GA-HospitalFirst. If the GA is presented as an optimization benchmark, this result deserves further discussion regarding the difference between the GA fitness function and the reported T_80/AUC objectives.

## Reviewer 2 — complete report

> This manuscript presents a set of steps using separate well-known methods taken to investigate contributing elements to disparities in post-earthquake power service restoration on a case study of Los Angeles. Specifically, it "combines established hazard, fragility, network-dependency, repair-logistic, and vulnerability-assessment components into a transparent workflow for evaluating earthquake-specific power-service recovery and community-level recovery disparities."
>
> The majority of the manuscript reads like an encyclopedia or dictionary of well-known methods. The manuscript is very long and very dull to read. The introduction is one short paragraph in length. The manuscript then immediately dives into a review of the literature without clear understanding of the manuscript's goals and motivation. The manuscript's contribution appears to be the study of factors in power service restoration that affect tract-level disparities in Los Angeles.
>
> The manuscript has some nice elements, but its methodological contributions are unclear despite many pages spent on methodologies and its findings are not particularly poignant or especially insightful. The application to Los Angeles sounds very interesting, as this city is very large, but the network is substantively reduced in size through assumptions designed to create a more aggregated and smaller problem instance, making it much less interesting. Moreover, the findings focus on the proposed methods and their effectiveness rather than on providing deeper understanding of or implications for disparities, how policies/regulations/strategies post-disaster can inadvertently create disparities, or how to avoid creating them.
>
> A number of additional comments/concerns follow that I hope will be helpful to the authors.
>
> 1. I recommend separating out the literature review into its own section and writing a proper introduction to motivate the paper.
>
> 2. The literature review does not elucidate what gaps exist in the literature that this manuscript will fill. Why is this manuscript important to publish given the existence of these earlier works? What haven't they done that will be done in this manuscript?
>
> 3. I also recommend moving most of the methods into appendices, as they do not appear to be novel, they are not well connected and they are taking away from what might be the real content of the manuscript.
>
> 4. The 3 questions on page 6 that guide the study are useful; however, the answers given for them at the end of the manuscript do not offer much we couldn't already guess from merely stating the questions. I expected much deeper and clearer findings with respect to these questions.
>
> 5. Table 1 is excellent.
>
> 6. Why identify the most critical substations? Does this align with the main goals of the paper?
>
> 7. I had difficultly following the normalized percolation curve discussion. Why does it need to be normalized? What is a redundantly meshed network? I'm not familiar with the idea of meshing.
>
> 8. Minor type page 19, "Second, time sequence helps" should be sequencing and "Third, path validity mandates [the or that the] crew…"
>
> 9. The use of a black-box genetic algorithm is very uninteresting. Why trust the GA? Why the GA? Where are the details of the GA or was it just a library?
>
> 10. Maybe the composite SVI score is the point of this paper and that portion of the paper could be the main focus?
>
> 11. The final LA network had 92 nodes with 318 edges. How large was the original network?
>
> 12. Many of the observations from the results are obvious. What is interesting that was found?
>
> 13. I found the logistics-aware strategy section difficult to follow. Logistics-aware or logistics-constrained makes me think that the effects of limited resources will be modeled, but this aspect is not well explained. It's also not novel.
>
> 14. Key: It was difficult to find findings within the solutions related to the main thing that the paper needs to show - the tradeoffs of using an "equity-informed, targeted restoration planning" approach. How much better would the outcomes have been in terms of reducing disparities if such a plan were used and at what cost and to whom? This may be buried in the results, but I struggled to find it.
>
> 15. Also a main finding is, "Overall, restoration-related assumptions primarily control the absolute duration of recovery, whereas topology-related assumptions mainly rest the robustness of service-propagation and tract-mapping boundaries." This is the final statement of the findings, yet I'm not sure what it really means or why the reader is concerned with these items. These are methods used in the study that are not necessarily well-adopted (or if they are, making that point would be very useful).
>
> 16. Overall, the conclusions section is helpful for identifying what the authors see as the final outcomes and seems to be quite inclusive. However, it also opens more questions, as most of the findings are specific to the methods that are suggested (e.g. the source-gated topology concentrates network vulnerability vs…). These were never findings that the reader was interested in, but rather a means to some deeper insight that the authors are offering. That is, the findings seem to come down to judgements about the pros and cons of offered methods that the manuscript applies rather than findings related to the overall point of the paper, which is never really made, but seems to be something related to how decisions affect different tracts disproportionately.

### Transcription notes for Reviewer 2

- Item 7 contains the original spelling **“difficultly.”**
- Item 8 begins with the original phrase **“Minor type page 19.”** This likely means “minor typo,” but it has not been silently corrected.
- Item 15 contains the original phrase **“mainly rest the robustness.”** It may have been intended as “mainly test the robustness,” but the received wording is retained.

## Separate Elsevier transfer-notification email — substantive text

> Dear Mr. Yi,
>
> We're sorry your submission was recently rejected. We have suggested some journals that may be a good fit for your manuscript.
>
> If you decide to transfer, then we'll send your files to your chosen journal, where you can still make revisions before completing your submission.
>
> If you are not interested in transferring your manuscript, you can use the 'Decline all' at the end of the list of suggestions and you will not receive further emails about transferring this manuscript.
>
> Please be assured that it is your decision what to do next. This transfer will not be completed without you taking further action.
>
> Publication of your manuscript is not guaranteed.
>
> Kind regards,
>
> Elsevier Transfer Your Manuscript Service

The private, manuscript-specific transfer link is intentionally omitted from this local record. It is an action link associated with the corresponding author’s submission.

## Transfer suggestions displayed by Elsevier

The transfer page stated that there were **five suggestions** for this manuscript. It also recognized the corresponding-author affiliation as **University of California Berkeley (Berkeley, United States of America)** and displayed each suggested journal as being in the institution’s publishing agreement.

| Suggested journal | Wording about guaranteed peer review on this offer | Impact Factor displayed | CiteScore displayed | Submission to first decision | Acceptance to publication | Publishing route and displayed APC |
|---|---|---:|---:|---:|---:|---|
| *Progress in Disaster Science* | **Guarantees peer review of your transferred manuscript** | 3.8 | 6.5 | 6 days | 3 days | Open access; US$2,280 excluding taxes |
| *Climate Risk Management* | No guaranteed-peer-review statement was shown on the supplied page | 5.0 | 10.2 | 4 days | 3 days | Open access; US$3,480 excluding taxes |
| *Reliability Engineering & System Safety* | No guaranteed-peer-review statement was shown on the supplied page | 11.0 | 19.1 | 7 days | 2 days | Open access US$4,590 excluding taxes, or subscription with no publishing charge |
| *Results in Engineering* | **Guarantees peer review of your transferred manuscript** | 7.9 | 7.3 | 6 days | 2 days | Open access; US$2,160 excluding taxes |
| *International Journal of Electrical Power & Energy Systems* | **Guarantees peer review of your transferred manuscript** | 5.0 | 13.0 | 11 days | 10 days | Open access; US$4,190 excluding taxes |

The page also provided a **Decline all** option. These journal metrics, speed figures, APCs, institutional-agreement labels, and guarantees are recorded as displayed; they are not acceptance probabilities and have not been independently converted into author out-of-pocket costs.

## Procedural facts verified from official sources

These points are included so that a local AI does not infer an incorrect submission state from the emails:

- Elsevier states that when an author accepts an Article Transfer Service offer, the manuscript files **including the review comments** are automatically submitted to the selected journal for consideration. The paper may be revised based on the reviews before the transfer submission is completed. Source: [Elsevier — How does the Article Transfer Service work for reviewers?](https://www.elsevier.support/publishing/answer/how-does-the-article-transfer-service-work-for-reviewers)
- The original reviewer comments transferring does not mean that the destination journal must adopt IJDRR’s decision, use the same reviewers, or accept the paper. The new journal conducts its own editorial assessment and peer-review process.
- Elsevier states that after transfer confirmation, a new submission is created at the destination journal but remains incomplete so that the author can revise it. Its current FAQ states that the author has **90 days from transfer confirmation** to revise and complete that submission. Source: [Elsevier — How can I transfer my rejected manuscript using Transfer Your Manuscript?](https://www.elsevier.support/publishing/answer/how-can-i-transfer-my-rejected-manuscript-using-transfer-your-manuscript)
- The same FAQ states that selecting **Decline all** cannot be undone. No transfer or decline action has been recorded in this document.
- If a later journal rejects the manuscript, it can be revised and submitted to another journal. The manuscript must not be simultaneously under consideration at multiple journals.
- The UC–Elsevier agreement currently says that eligible UC corresponding authors receive a reduced APC for most Elsevier journals, an automatic first US$1,000 contribution from UC Libraries, and may request full APC coverage when grant funds are absent or insufficient. Eligibility, journal inclusion, and the final payment workflow still require confirmation. Source: [University of California — Elsevier Transformative Open Access Agreement](https://osc.universityofcalifornia.edu/for-authors/publishing-discounts/elsevier-oa-agreement/)

## Instructions for technical use of this record

When comparing these reports with the local project:

- Treat every reviewer concern as a question to audit, not as proof of a coding error.
- Distinguish among: an actual implementation problem; an assumption needing validation; an analysis that can be added from existing outputs; and a wording, framing, or scope problem.
- Verify which manuscript version generated the reported figures and tables. The cloud-side review previously examined a file named **LA Grid Paper Revised_20260720.pdf**, but it was not confirmed to be byte-identical to the version submitted on 23 July 2026.
- For every technical conclusion, cite the relevant local manuscript page, source file, function or configuration key, and output. State whether the conclusion comes from reading code, inspecting saved output, or executing a diagnostic run.

