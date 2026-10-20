# Execution record

## Sequence

1. Verified source integrated HEAD locally/remotely: b307e6deafc054864787a3db63ad95218be91659.
2. Created independent branch refs/heads/1021 in `_1021`; no reset, merge or force-push.
3. Pushed protocol e10957e0f96be5d80c1e7d4781a84e52afcb6d6b.
4. Stopped preflight for a source-worktree packet rename; independently proved
   the renamed PDF was byte-identical, documented it without modifying it.
5. Pushed implementation/input registry 0c344e7d8b5e8cc0f6cc073e1d8c2bcfdf8d785d.
6. Eight pre-experiment method tests passed; two-replicate smoke run was marked
   PILOT_NOT_FULL and is excluded from all scientific conclusions.
7. Full registered experiment ran in 224.32 s; exact-seed full replay in 221.85 s.
   Seventeen core arrays/CSV payloads are byte-identical across both runs.
   Replay repeats identical experiments; it does not increase effective B.
8. Independent verification recalculated all 40 observed WCSS, 1,024 null WCSS
   and draw hashes, 700 prediction-strength directions and 4,000 bootstrap
   Jaccards. All 950 external protected files and source status/index matched.
9. Eleven final tests passed; compileall and diff checks passed. Three actual
   vector PDFs were rendered and inspected at 7.2-inch width.

## Corrections during QA, not analytical changes

- The independent WCSS check initially used means of final reassigned labels.
  sklearn tolerance stopping can leave these slightly different from the
  actual fitted centers. The check was corrected to verify both nearest-center
  assignments and actual fitted-center WCSS; the residual re-centering gain is
  reported. No fitted result was changed and no tolerance was relaxed.
- Independent PCA null replay initially used unrestricted BLAS threading,
  producing a different byte hash from tiny floating-point differences.
  Applying the already registered one-thread limit reproduced every draw
  exactly; all WCSS and hashes pass, not merely approximate comparisons.
- Changes after the initial implementation push added descriptive population
  and quartile columns, portable QA, verification and plotting/reporting only.
  No selection rule, metric, K range, seed or repetition budget was changed
  after results were examined.
- Literal JSON/XML/TXT QA bytes are retained through Git without automatic
  line-ending conversion. Python and Markdown sources use LF.

## Remote delivery

verify_delivery.py fetches all newly committed LFS payloads into a new EMPTY
object store, compares actual bytes/hash/size with the committed OID and local
file, and checks both 1021 and unchanged October 14 remote HEADs. It does not
accept pointer existence as proof of delivery.

REMOTE_DELIVERY_VERIFICATION.json identifies the payload-bearing result commit
that was verified. A later receipt-only commit may record that verification;
rerunning verify_delivery.py --no-write verifies the final HEAD including the
same payloads without creating another self-referential receipt commit.

No publication figure, caption, manuscript, scientific authority, source data,
physical simulation or restoration calculation was edited. The original
source-worktree filename-only change remains exactly as found and is not
claimed to be clean. The independent 1021 delivery is committed separately.
