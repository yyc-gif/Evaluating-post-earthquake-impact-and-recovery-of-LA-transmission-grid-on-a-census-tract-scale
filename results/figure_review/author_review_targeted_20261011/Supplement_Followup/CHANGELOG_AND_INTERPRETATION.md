# Changes and interpretation

| Figure | Targeted change | Preserved |
|---|---|---|
| S03 | Map point opacity 0.62; remove ten six-digit axis labels and the word ID. | Point locations and sizes; all directed travel entries, station order, linear color scale and panel size. |
| S06 | Label B as combined threshold/source removal; identify C/D as retaining source connectivity. | All nine means/ranges and the cutoff panel. No new gate evaluation. |
| S07 | Both A/B have focal-policy and other-policy views, with local keys and the same Unconstrained reference. Explain C as source access from a functional station. | Every saved curve ordinate; full-network versus fixed-path coding; static maps, probabilities and linear color ranges. Height increases from 220 to 227 mm to retain readable text and native map size. |
| S10 | Change only the population palette in C to subdued neutral gray. | Log normalization, population values, geometries, station locations, first-five identities, ranks and names; A/B. |
| S11 | Shared signed-log colors, linear within +/-0.10 h and logarithmic beyond; original symmetric hour limits. | All 96 mean differences, four scenarios, six policy rows, four metrics and printed hour values. No clipping or separate scenario scales. |

S06 B compares production station service, e = f * F_0.50 * C_14Core, with e = f. Thus both the functionality threshold and source requirement are removed. The 0.05/0.75 threshold comparisons retain source connectivity. The actual saved summaries and registered design contain no threshold-removal-only or source-removal-only cases. Those effects cannot be separated by relabeling the existing joint contrast or subtracting unrelated scenarios. This package retains the available evidence and states that limitation.

For S07 C, conditional source reachability is P(a path to at least one active Core source | target station functional). Other stations and sources can still fail. It separates upstream path availability from the target station's own failure probability. A/B instead use the joint event of target functionality and source connection under saved recovery trajectories. A fixed-path probability refers to one precomputed path; full-network connectivity includes any viable route. None measures delivered electricity or electrical adequacy.

S07 A previously showed two policies, while B showed six selected policies plus Unconstrained. Both now show the four focal policies in the left view and Betweenness-first/Random in the right; Unconstrained appears in both. Each view's policy key applies to both rows. A's separate line-style key distinguishes quantities, not policy importance. Legend entries are generated directly from plotted policy lists, without marker symbols absent from the curves.

The actual current S03 displays the full directed matrix, despite an obsolete lower-triangle sentence in its caption. The proposed caption corrects this mismatch. The two directions are not asserted to be redundant or equal. Only identifiers are removed in this round.

S11's new colors are deliberately nonlinear. A twofold color-distance change must not be read as a twofold hour difference. Use the unchanged cell numerals and hour ticks for magnitudes. The heatmap still does not display uncertainty, and cross-hazard differences are not pure hazard-intensity effects.
