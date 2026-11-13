# Preservation and execution scope

Starting implementation branch: `submission/ijdrs-five-main-20261112`, from `a6847bda22a49b13ba0ef2fa309dfb9cdb994909`. Accepted artwork remains anchored to `68c83459e60ef31f7e86af9155d5a11e1680235d`.

Authorized changes are confined to the independent package, its new builder and tests, and scoped text attributes. No original production builder, original caption registry, manuscript, scientific input or numerical output is edited. No simulation, scheduling, optimization, uncertainty estimation or clustering is executed.

All 32 original numbered PDF/PNG files were checked against the actual frozen Git LFS payload hashes. Original captions and figure manifest were compared with the pinned Git content. This establishes preservation of the available artwork, not a new full rehash of the historical 950-file scientific inventory. Some historical scientific payloads are absent in this sparse worktree; their preservation is established only by unchanged Git paths, not by an invented full local byte audit.

Both actual author-manuscript copies remain SHA256 `39df3b9bf73722ae1dbc88cb015b4ef9ece8322c71bf7b84431476b8150314ac`. Neither is copied into this package. The registered paragraph review includes accepted-visible tracked text without changing the Word file.

The original review worktree retains its exact pre-existing untracked entries and an empty staged diff:

```text
?? .remote-lfs-verify/
?? results/figure_review_s6_main4_20261107/QA/Fig01_Stage5_source_clip.png
?? tmp/
```

The original review branch remains `68c83459e60ef31f7e86af9155d5a11e1680235d`; the previous universal-artwork branch remains `a6847bda22a49b13ba0ef2fa309dfb9cdb994909`. Neither is merged, reset or force-pushed. Intermediate renders and test scratch files are ignored and excluded from delivery.
