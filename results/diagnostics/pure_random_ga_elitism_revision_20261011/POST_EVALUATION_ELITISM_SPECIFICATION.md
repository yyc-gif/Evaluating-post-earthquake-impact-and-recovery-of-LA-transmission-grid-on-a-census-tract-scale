# Post-evaluation survival specification

Generate exactly100 children with unchanged parent selection/OX/swap. Evaluate them in index order through the private cache. Count all new distinct scores including the last child. Update global best-observed at every actual new score, before any survival replacement.

Previous elite is selected by the unchanged current-generation rank; its chromosome/fitness is stored across interrupted evaluations. If its exact chromosome appears among children, skip insertion. Otherwise choose minimum fitness, breaking worst-score ties by lowest child index. Insert only if elite fitness >= worst fitness; equal-fitness distinct chromosomes therefore replace the first worst. If all offspring are strictly better, skip. No tie-related RNG draw. Population size and permutation validity stay unchanged.

If the distinct budget ends at an unseen child, preserve the scored prefix and unfinalized pending elite. Do not count a complete generation or insertion. After all children are scored, finalize once even when the final unique score consumes the budget. Repeating that budget is idempotent; extending it resumes the exact next operation.

Legacy discarded children are measured separately after search, not fed back into either algorithm. Generated, attempted, distinct, cached, generation, insertion/presence/all-better and strict-improvement counts remain distinct. Conditional elite survival is not global-archive injection.
