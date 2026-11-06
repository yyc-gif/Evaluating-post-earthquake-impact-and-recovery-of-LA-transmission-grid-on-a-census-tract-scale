# Contribution 1 Results

This package evaluates repair-order mechanisms using the frozen 2pc50/C57_D1 archives. It does not rerun physical damage, repair scheduling, service simulations, or GA optimization.

- `PROTOCOL.md`: analysis rules registered before the paired perturbation experiment.
- `SCIENTIFIC_DECISION.md`: findings and qualified scientific conclusion.
- `MECHANISM_EVIDENCE_SUMMARY.json`: compact machine-readable result summary.
- `REPRODUCIBILITY_AND_LIMITATIONS.md`: identities, checks, source limitations, and commands.
- [Executable analysis](../../src/la_grid/diagnostics/c1_mechanism_actionability.py).
- `FIG_MECHANISM_UNLOCK.pdf/.png`: event-level source unlocking by frozen strategy.
- `FIG_MARGINAL_REPAIR_BENEFIT.pdf/.png`: paired local priority perturbation estimates.
- `FIG_EVENT_UNLOCK_ILLUSTRATIONS.pdf/.png`: three verified pre/post network-state examples.

Full realization/event/perturbation CSV outputs are generated locally by the script but are intentionally not tracked in Git under the project’s intermediate-data storage rule.
