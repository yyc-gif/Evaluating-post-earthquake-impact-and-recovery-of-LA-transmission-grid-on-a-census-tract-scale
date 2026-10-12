# Pure-random parameter evidence admission

The five requested historical families were read as planning-only evidence; exact source hashes and table columns are in HISTORICAL_EVIDENCE_INVENTORY.csv. No validation outcome enters parameter selection.

| Choice | Purpose and prior rationale | Transfer to pure random | Required controlled evidence |
| --- | --- | --- | --- |
| Population100 | Parallel exploration bounded by distinct work | Earlier50/250 mixes changed heuristic/prior/neighbor counts; do not transfer | P50/P250 random-only; common-prefix initialization, fewer generations at larger N |
| OX0.80 | Copy a contiguous priority block, cyclically preserve other-parent order; valid permutation | Existing fixed implementation and working pure-reference receipts support feasibility, not rate optimality | 0.60/0.95 with all other choices fixed |
| Swap0.10 | Small permutation move, no repair operation needed | Prior operator/rate comparisons used quality initialization | 0.05/0.20; inversion/insertion at0.10 to resolve move-scale dependence |
| Tournament3 | With-replacement rank pressure without fitness rescaling | Earlier T2 deterioration and T5 interactions are background-specific | T2/T5 from same random pools |
| Elite1 | Preserve current-population best; distinct from passive output archive | Fixed0/1/2/3 studies retained inherited/heuristic information | E0/E2 random-only, all with identical passive retention |
| 100k/20seeds | Finite evaluation budget and independent optimizer replication | Direct20 pure-reference records and10 continued prefixes are admissible | Reuse20k/50k/100k/250k/500k; continuations are not new replicates |
| Adaptation/restart/crowding off | Keep one reproducible basic GA, no extra dynamics | Direct reference works; disabled mechanisms not a superiority claim | No new enabled search: not needed to defend a working simple reference |

Literature supports mechanisms, not these numerical optima. Blickle & Thiele, TIK Report11 revised Dec1995, describes tournament selection intensity/diversity: https://tik-old.ee.ethz.ch/file/6c0e384dceb283cd4301339a895b72b8/TIK-Report11.pdf . Eiben, Hinterding & Michalewicz1999 distinguish parameter tuning/control: https://cs.adelaide.edu.au/~zbyszek/Papers/self9.pdf , DOI10.1109/4235.771166. Vazquez & Whitley2000 compare order-based scheduling operators: https://www.cs.colostate.edu/~genitor/2000/ppsn2000.pdf . No paper is cited as proving P100/CX.8/M.1/T3/E1 optimal here. Source code, not a generic textbook description, defines this exact OX and tie rules.

The old93.06% inherited-gain fraction is excluded from claims of independent GA efficacy. Existing reference initialization and budget evidence is reused, not rerun. Twelve genuine unresolved one-factor alternatives enter the engineering screen; three consequential contrasts enter separately seeded confirmation by the precommitted absolute-effect rule. No alternative crossover or broad enabled-mechanism grid is scientifically necessary for this bounded audit.
