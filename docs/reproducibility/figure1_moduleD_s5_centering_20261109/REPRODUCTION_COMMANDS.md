# Reproduction

Run from the repository root with the project Python environment:

```powershell
python src/la_grid/plotting/build_s6_main4_review.py
python -m pytest tests/test_s6_main4_promotion_20261107.py -q
python docs/reproducibility/figure1_moduleD_s5_centering_20261109/verify_delivery.py
```

The canonical builder updates the isolated `results/figure_review_s6_main4_20261107/` suite and its mirror. It reads the pinned source suite and manifest-bound S5 plot/audit JSON; it does not run simulations, scheduling, or optimization. The underlying event archives are manifest-bound local dependencies and are not included in a clean Git clone.
