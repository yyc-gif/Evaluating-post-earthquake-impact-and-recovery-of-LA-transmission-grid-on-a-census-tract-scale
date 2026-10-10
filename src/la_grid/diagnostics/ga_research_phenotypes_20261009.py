"""Audit retained final chromosomes for exact score and scheduling equivalence."""
from __future__ import annotations
import hashlib
import json
import numpy as np
import pandas as pd

from la_grid.diagnostics.ga_research_collect_20261009 import ROOT, long_path, save
from la_grid.diagnostics.ga_init_param_20261009 import load
from la_grid.revision.r1_equity_amendment_execute import execution_context
from la_grid.diagnostics.ga_search_budget_sensitivity import identity

OUT = ROOT / "continuation"


def main():
    k, _, _, model = load()
    context, decoder, _ = execution_context(k.ids)
    origins = decoder.origins(context["origins"])
    receipt = hashlib.sha256(json.dumps(model, sort_keys=True).encode()).hexdigest()
    sequences = json.loads(long_path(OUT/"ALL_FINAL_SEQUENCES_BY_SHA256.json").read_text())
    runs = pd.read_csv(long_path(OUT/"SEED_LEVEL_SEARCH_RESULTS.csv"))
    path = OUT/"FINAL_PHENOTYPE_CACHE.json"
    cache = json.loads(long_path(path).read_text()) if long_path(path).exists() else dict(model_identity_sha256=receipt, records={})
    assert cache["model_identity_sha256"] == receipt
    new = 0
    for sha, seq in sequences.items():
        assert identity(seq) == sha
        if sha in cache["records"]:
            continue
        order = decoder.order(seq)
        completion = []
        travel = []
        crews = []
        for b in range(64):
            finish, _, legs, crew, *_ = decoder.decode(order=order, damage=k.damage[b],
                duration=k.duration[b], origins=origins)
            completion.append(finish)
            travel.append(legs)
            crews.append(crew)
        finish_bytes = np.nan_to_num(np.array(completion), nan=np.inf).astype("<f8").tobytes()
        travel_bytes = np.nan_to_num(np.array(travel), nan=np.inf).astype("<f8").tobytes()
        crew_bytes = np.array(crews).astype("<i8").tobytes()
        score = -k.score(seq)
        expected = runs.loc[runs.sequence_sha256.eq(sha), "planning_loss_hr"]
        max_error = float(np.max(np.abs(expected-score)))
        assert max_error < 1e-8, (sha, score, expected.tolist())
        cache["records"][sha] = dict(sequence_sha256=sha,
            completion64_sha256=hashlib.sha256(finish_bytes).hexdigest(),
            completion_travel_crew64_sha256=hashlib.sha256(finish_bytes+travel_bytes+crew_bytes).hexdigest(),
            compiled_loss_hr=float(score), max_archived_score_error_hr=max_error)
        new += 1
    save(path, cache)
    df = pd.DataFrame(cache["records"].values())
    active = df[df.sequence_sha256.isin(sequences)]
    active.to_csv(long_path(OUT/"FINAL_CHROMOSOME_PHENOTYPES.csv"), index=False)
    joined = runs.merge(active, on="sequence_sha256", validate="many_to_one")
    summary = joined.groupby(["batch","configuration"]).agg(
        final_records=("seed","count"), unique_chromosomes=("sequence_sha256","nunique"),
        unique_completion_phenotypes=("completion64_sha256","nunique"),
        unique_completion_travel_crew_phenotypes=("completion_travel_crew64_sha256","nunique")).reset_index()
    summary.to_csv(long_path(OUT/"FINAL_METHOD_PHENOTYPE_SUMMARY.csv"), index=False)
    groups = active.groupby("completion64_sha256").agg(
        chromosome_count=("sequence_sha256","count"), minimum_loss_hr=("compiled_loss_hr","min"),
        maximum_loss_hr=("compiled_loss_hr","max")).reset_index()
    assert np.max(groups.maximum_loss_hr-groups.minimum_loss_hr) < 1e-8
    groups[groups.chromosome_count>1].to_csv(long_path(OUT/"SCHEDULING_EQUIVALENT_FINAL_GROUPS.csv"), index=False)
    save(OUT/"FINAL_PHENOTYPE_QA.json", dict(status="ALL_FINAL_ARCHIVED_SCORE_AND_COMPLETION_AUDIT_PASS",
        final_search_records=len(runs), unique_chromosomes=len(active),
        unique_completion_phenotypes=int(active.completion64_sha256.nunique()),
        repeated_chromosome_final_records=int(len(runs)-len(active)),
        max_absolute_archived_score_error_hr=float(active.max_archived_score_error_hr.max()),
        new_mean_score_audit_calls=new, total_retained_mean_score_audit_calls=len(cache["records"]),
        total_retained_native_schedule_decodes=64*len(cache["records"]),
        optimizer_runs_reexecuted=0, physical_samples_generated=0,
        interpretation="Final solutions only; distinct seed/configuration outcomes remain separate even when their final chromosomes coincide"))
    print("PHENOTYPES", len(active), active.completion64_sha256.nunique(), "NEW_AUDITS", new, flush=True)


if __name__ == "__main__":
    main()
