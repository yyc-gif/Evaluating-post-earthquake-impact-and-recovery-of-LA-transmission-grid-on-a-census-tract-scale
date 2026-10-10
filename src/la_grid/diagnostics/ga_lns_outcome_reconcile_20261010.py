"""Reconcile completed v1/v2 scheduling-aware LNS output WITHOUT new score calls.

Workflow downloads original GitHub Actions artifacts into separate directories.
This script checks all 160 full-budget search outcomes, exact 92-ID sequence
identity, checksum, and expensive budgets; then computes paired outcome and
mechanism diagnostics. No scientific model loading, no resampling or tuning.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.stats import t as student_t

SOURCE_RUNS = {"v1": 38033702030, "v2": 38034064901}
EXPECTED = {"v1": set(range(820,840)), "v2": set(range(920,940))}
METHODS = {
    "v1": ("ga_baseline","iterated_local","lns_event_route","lns_random_bundle"),
    "v2": ("ga_baseline","iterated_local","lns_repair_route","lns_repair_random"),
}
WARM_J = 33.03813174326729
FROZEN_J = 32.997840773882714
BUDGET = 100000
BOOTSTRAP_ITERATIONS = 20000
BOOTSTRAP_SEED = 2026101004

def record_hash(order):
    return hashlib.sha256(("\n".join(order)+"\n").encode()).hexdigest()

def collect(version,root):
    expected=EXPECTED[version]
    rows={}
    seenfile={}
    for p in root.rglob("ALL_METHODS.json"):
        data=json.loads(p.read_text(encoding="utf-8"))
        if data.get("status")!="COMPLETE":continue
        seed=int(data["seed"])
        if seed not in expected or int(data["budget"])!=BUDGET: continue
        if seed in rows:
            raise AssertionError(f"Duplicate complete result: {version} seed {seed}: {p} and {seenfile[seed]}")
        values=data["methods"]
        assert len(values)==4, (p,len(values))
        cases={}
        for v in values:
            method=v["method"]
            assert method not in cases, (p,method)
            assert method in METHODS[version], (p,method)
            assert int(v["seed"])==seed and int(v["budget"])==BUDGET
            assert int(v["distinct_evaluations"])==BUDGET
            assert v.get("completed_budget",True)
            seq=v["best_sequence"]
            assert len(seq)==92 and len(set(seq))==92
            assert record_hash(seq)==v["sequence_sha256"],(p,method)
            assert np.isfinite(float(v["search_best_loss_hr"]))
            assert int(v["attempted_evaluations"])>=BUDGET
            cases[method]=v
        assert set(cases)==set(METHODS[version]),(p,set(cases))
        rows[seed]=cases
        seenfile[seed]=str(p)
    assert set(rows)==expected, (version, "missing",sorted(expected-set(rows)),"unexpected",sorted(set(rows)-expected))
    ids=None
    for cases in rows.values():
        for record in cases.values():
            names=set(record["best_sequence"])
            if ids is None:ids=names
            assert ids==names
    return rows,seenfile

def mean(x):return float(np.mean(x))
def details(r):
    arr=np.asarray(r,dtype=float)
    return dict(mean=mean(arr),median=float(np.median(arr)),
      sample_sd=float(np.std(arr,ddof=1)),
      minimum=float(np.min(arr)),maximum=float(np.max(arr)))

def paired(values,comparison_family=3):
    d=np.asarray(values,dtype=float)
    n=len(d)
    avg=d.mean()
    sd=np.std(d,ddof=1)
    half=float(student_t.ppf(1-0.05/(2*comparison_family),n-1)*sd/np.sqrt(n))
    r=np.random.default_rng(BOOTSTRAP_SEED)
    bootstrap=np.mean(d[r.integers(0,n,size=(BOOTSTRAP_ITERATIONS,n))],axis=1)
    lo,hi=np.quantile(bootstrap,[.025,.975])
    return dict(n=int(n),mean_delta_hr=float(avg),median_delta_hr=float(np.median(d)),
        sd_paired_hr=float(sd),simultaneous_95=[float(avg-half),float(avg+half)],
        pointwise_t95=list(map(float,[avg-student_t.ppf(.975,n-1)*sd/np.sqrt(n),
                                     avg+student_t.ppf(.975,n-1)*sd/np.sqrt(n)])),
        seed_bootstrap_95=[float(lo),float(hi)],
        wins=int(np.sum(d< -1e-10)),losses=int(np.sum(d>1e-10)),
        ties=int(np.sum(abs(d)<=1e-10)),
        multiplicity_family_size=comparison_family)

def summary(version,records):
    labels=METHODS[version]
    losses={label:np.array([records[seed][label]["search_best_loss_hr"] for seed in sorted(records)])
            for label in labels}
    methods=[]
    for name in labels:
        recs=[records[seed][name] for seed in sorted(records)]
        losses_arr=losses[name]
        mean_attempts=mean([r["attempted_evaluations"] for r in recs])
        mean_wall=mean([r["elapsed_wall_seconds"] for r in recs])
        global_best_counts=[]
        for r in recs:
            # Ignore setup-incumbent improvements at evaluations 1..8.
            # Count strictly new best-so-far values below the inherited best.
            global_best_counts.append(sum(
                1 for item in r.get("strict_improvements",[])
                if item["best_loss_hr"] < WARM_J - 1e-9))
        extra={}
        if name.startswith("lns_"):
            fields=(("v1",["strict_moves","neutral_moves","event_bank_refreshes",
                           "source_reconnection_events_sampled","event_bundle_proposals",
                           "random_proposal_fallbacks"]),
                    ("v2",["accepted_strict_repairs","accepted_neutral_repairs",
                           "route_macros","conventional_local_macros",
                           "event_snapshot_refreshes","event_candidates_built",
                           "actual_repair_candidates_evaluated"]))
            fields=dict(fields)[version]
            extra.update({key+"_mean":mean([r.get(key,0) for r in recs])
                          for key in fields})
            extra["mean_global_best_improvements"]=mean(global_best_counts)
            extra["runs_with_zero_global_best_improvements"]=sum(
                1 for n in global_best_counts if n==0)
            sizes={}
            key="bundle_size_proposal_counts" if version=="v1" else "bundle_size_macro_counts"
            for row in recs:
                for k,v in row.get(key,{}).items():
                    sizes[str(k)]=sizes.get(str(k),0)+int(v)
            extra["bundle_size_counts"]=sizes
        methods.append(dict(method=name,loss_hr=details(losses_arr),
            mean_attempted_evaluations=mean_attempts,mean_duplicate_fraction=1-BUDGET/mean_attempts,
            mean_wall_seconds=mean_wall,
            runs_better_than_old_warm=int(np.sum(losses_arr<WARM_J-1e-9)),
            runs_better_than_frozen_ga=int(np.sum(losses_arr<FROZEN_J-1e-9)),
            **extra))
    source=labels[2];random_control=labels[3]
    comp=[]
    for candidate,reference in [(source,random_control),(source,"ga_baseline"),
                 (source,"iterated_local"),(random_control,"iterated_local"),
                 ("iterated_local","ga_baseline")]:
        stats=paired(losses[candidate]-losses[reference],3)
        stats.update(method=candidate,reference=reference)
        comp.append(stats)
    return dict(source_actions_run_id=SOURCE_RUNS[version],
        seed_set=sorted(records),case_count=len(records)*4,
        distinct_budget_per_case=BUDGET,methods=methods,contrasts=comp)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--v1",type=Path,required=True)
    p.add_argument("--v2",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    d1,p1=collect("v1",a.v1)
    d2,p2=collect("v2",a.v2)
    r={"status":"ALL_160_COMPLETE_ACTIONS_ARTIFACTS_RECONCILED",
       "source_base_commit":"409693a68a099e6c1ec2fee093b3bfd2ecf80dd6",
       "v1":summary("v1",d1),"v2":summary("v2",d2),
       "no_new_objective_evaluations":True,"no_new_physical_realizations":True,
       "formal_candidate_unchanged":True,
       "method_comparison_same_seed_within_study":True,
       "methods_not_same_random_streams":True,
       "v1_v2_cohorts_distinct":True,
       "statistical_scope":"Optimizer random seeds conditional on fixed already-trained 64 planning realizations"}
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/"LNS_160_RUN_AUDIT.json").write_text(json.dumps(r,indent=2)+"\n",encoding="utf-8")
    lines=["# Scheduling-aware LNS negative-outcome audit","",
       "All 160 case-seed outcomes retained from completed original GitHub Actions artifacts; none rerun. Exact candidate SHA-256, 92-element permutation, seed, budget and program completion verified.",
       "", "**Not a new-physics/generalization test. Both algorithms were developed using the same 64 planning states. Lower loss is better.**",""]
    for version in ["v1","v2"]:
        item=r[version]
        lines += [f"## {version.upper()}: run {item['source_actions_run_id']}","",
                  "| Method | Mean loss (h) | SD (h) | Min loss (h) | Mean wall (s) | Mean attempts | Improved prior warm |",
                  "|---|---:|---:|---:|---:|---:|---:|"]
        for x in item["methods"]:
            l=x["loss_hr"]
            lines.append(f"| {x['method']} | {l['mean']:.9f} | {l['sample_sd']:.9f} | {l['minimum']:.9f} | {x['mean_wall_seconds']:.1f} | {x['mean_attempted_evaluations']:.0f} | {x['runs_better_than_old_warm']}/20 |")
        lines += ["", "| Pair (first − second) | Mean delta (h) | Bonferroni 95% interval (h) | First wins | Second wins |",
                  "|---|---:|---:|---:|---:|"]
        for c in item["contrasts"]:
            lines.append(f"| {c['method']} − {c['reference']} | {c['mean_delta_hr']:+.9f} | [{c['simultaneous_95'][0]:+.9f}, {c['simultaneous_95'][1]:+.9f}] | {c['wins']} | {c['losses']} |")
        lines += ["","### Mechanistic counters",""]
        for entry in item["methods"][2:]:
            lines.append(f"**{entry['method']}**: "+
                "; ".join(f"{k}: {str(v)[:120]}" for k,v in entry.items()
                    if k.endswith("_mean") or k.startswith("runs_with_zero_") or k=="bundle_size_counts"))
            lines.append("")
    lines += ["## Interpretation and next action","",
      "- Source-event route proposal targeting is **not competitive as implemented**; LNS v1 and v2 should be published as negative diagnostics rather than promoted to a formal policy.",
      "- v2 random-bundle control's advantage over event-route LNS is evidence that the *current source-path bundling/repair proposal* is ineffective, not proof that network-aware LNS is intrinsically unsuitable.",
      "- Because objective is the average over the reused 64 training states, selecting proposal bundles based on source reconnection in four sampled individual states can lead to negative cross-realization transfer. This is a **hypothesis**, not established by final scores alone.",
      "- Accepted current-solution improvements need not improve the global best. Inspect strict-improvement trajectories separately.",
      "- Before new optimizer runs, perform a bounded *proposal-level* comparison from a fixed common sequence: event-sample benefit versus mean64 benefit and route-vs-random bundles with identical repair candidates/budgets.",
      "- Do not spend additional budget on the unchanged v1/v2, infer equivalent performance from unresolved contrasts, or inspect the untouched 2000-realization independent cohort for method selection.",
      "- No original GA candidate, objective function, physical samples or manuscript outputs changed.",""]
    (a.output/"LNS_160_RUN_AUDIT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("LNS_160_RUN_AUDIT_COMPLETE",json.dumps({k:{"cases":r[k]["case_count"],"methods":len(r[k]["methods"])} for k in ["v1","v2"]}),flush=True)

if __name__=="__main__":main()
