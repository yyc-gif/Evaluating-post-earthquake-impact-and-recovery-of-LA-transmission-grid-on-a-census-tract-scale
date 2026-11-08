# Figure delivery package verification

The package is built exclusively from committed figure-suite sources at `0cefb5440dbf918b659a5e2f3550cdeb83998d7b`. It includes 16 separate artwork PDF/PNG pairs with no captions embedded, the standalone caption registry, and the latest complete figure/caption PDF. No scientific data or figure content is recalculated.

```powershell
python docs/reproducibility/figure_delivery_20261108/package_delivery.py
python -m pytest tests/test_figure_delivery_20261108.py -q
```

The ZIP has 36 members, a SHA-256 inventory and a verified CRC table. Its SHA-256 and byte size are recorded in `results/figure_delivery_20261108/PACKAGE_QA.json`.
