# Candidate manuscript text

Discussion draft for the LA grid study, 23 November 2026. Paragraphs are proposed for the existing manuscript structure. Section and figure references follow the local 11 November draft. The figure name below is a placeholder pending review.

## Section 2.3 Focus of this study

Earthquake damage and network connectivity can produce spatially uneven electric service recovery before dispatch constraints are applied. Once recovery is constrained, the choice of repair priority may change which communities experience the largest additional losses. Previous Los Angeles studies have modeled spatial differences in restoration and allocated earthquake-related load shedding to census tracts. Simulation studies of hurricane outages also show that population-based and vulnerability-based repair priorities affect household hardship differently. These precedents motivate distinguishing the geographic distribution of service loss from the distribution of changes under a specific recovery arrangement (Çağnan et al., 2006; Cheng, 2023; Cheng et al., 2024; Esmalian et al., 2022).

We compare the unconstrained recovery deficit, the total deficit under each tested repair priority, and the added deficit relative to the matched unconstrained case. The three quantities allow us to ask how often a fixed number of tracts selected by baseline or total deficit also captures the tracts with the largest added deficit, and how this coverage changes with repair priority. This comparison complements the social vulnerability analysis and helps interpret the community recovery profiles in the third research question.

Optional replacement for the final research question if the group wants to name the comparison explicitly:

> How do baseline and added service deficits identify different sets of high-burden communities across repair priorities, and how do these patterns relate to social vulnerability and community recovery profiles?

## Results

Suggested placement: Section 4.5, immediately before the community profiles.

Under the earthquake scenario with a 2% probability of exceedance in 50 years and the reference restoration resource level, we compared the modeled service deficit integrated over 480 hours in 2,315 census tracts. For each priority, the added deficit was the difference between the constrained total and the matched idealized unconstrained deficit. The equal mean across the five priorities had a Pearson correlation of 0.027 with the baseline deficit (population weighted, 0.042). The weak average association reflected opposing contributions to the covariance. Degree-first contributed +2.111 h² to the five-priority mean covariance, while the other four contributions summed to −1.764 h². Recomputing the mean and its correlation without Degree-first changed Pearson's r to −0.162 (population weighted, −0.150).

The baseline deficit screen captured 212 of the 579 tracts in the highest quarter of mean added deficit (36.6%), leaving out 367 tracts with 1,432,501 residents. The mean total deficit screen captured 334 (57.7%) and omitted 245 tracts with 963,079 residents. For individual priorities, baseline coverage ranged from 20.4% under Hospital-first to 62.5% under Degree-first. Coverage from the corresponding total deficit ranged from 51.3% to 76.5%, with the same priorities at the two endpoints. For the five-priority mean, the total deficit coverage advantage held at the top 20%, 25%, and 30% of tracts and in all 47 omissions of one 10 km block at a time. Each comparison used equally sized lists and recomputed the rankings in the retained sample.

## Discussion

The value of distinguishing these metrics is the ability to quantify which communities a given screening rule would leave out. The baseline screen reflects losses under idealized unconstrained repair. Total deficit captures the burden under the modeled restoration policy. Added deficit identifies where the gap relative to the matched reference is largest. With the same number of tracts on the list, the total deficit captured more high added deficit tracts than the baseline deficit, yet missed 42.3% of the five-priority target group. Because total deficit includes the added component, the gain is a descriptive feature of the joint rankings. It provides no independent test of predictive performance. Coverage also changes with the restoration rule, so the five-priority mean alone is insufficient to describe the geography of added deficit across policies.

These findings extend the existing comparisons of social vulnerability and total deficit by describing who would be omitted when those comparisons are guided by a burden screen chosen for a different question. In this scenario, the signed Q4 minus Q1 difference in population-weighted mean deficit was negative for both the baseline and the five-priority increment. The community profiles summarize variation in the two measures as inputs to the clustering and do not independently establish distinct mechanisms. The added deficit is conditional on the simulated damage, assumed repair durations, source connectivity, resource level, and priority rules. The analysis supports discussing which modeled burden a screening exercise seeks to capture. It cannot isolate individual logistical effects, determine household outage hardship, or establish that the same lists would emerge under other hazards or resource settings.

## Reference cross-check

The comparison with Cheng's dissertation is supported by Chapters 2–3. The exact equivalence of those chapters to the final 2024 IEEE Access article remains to be checked against that article's figures and methods. For the 2006 LA restoration article we verified the abstract and used its 2004 technical precursor for detailed methods. See the [contribution and literature note](CONTRIBUTION_REVIEW.md) for the reviewed experiments and remaining verification.
