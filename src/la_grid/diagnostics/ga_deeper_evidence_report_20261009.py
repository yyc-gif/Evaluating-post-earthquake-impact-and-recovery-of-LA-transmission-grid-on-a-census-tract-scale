"""Reconcile and analyze only completed GA method/alternative search records.

Input raw records are GitHub Actions artifacts. Never regenerate scientific
physical samples or score a new chromosome in this report.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import t as student_t
from la_grid.paths import REPO_ROOT

ROOT=REPO_ROOT/"results/diagnostics/ga_deeper_research_20261009"
IMPACT_FIRST=33.57830255999924
RAW_SPEC={
    "factorial":(range(200,212),19,"results"),
    "factorial_confirm_100k":(range(400,420),11,"cases"),
    "alternative":(range(300,320),3,"methods"),
}

def records(name):
    seeds,ncase,key=RAW_SPEC[name]
    values={}
    for seed in seeds:
        p=ROOT/name/f"seed_{seed}"/("ALL_METHODS.json" if name=="alternative" else "ALL_CASES.json")
        if not p.exists():
            raise FileNotFoundError(f"Incomplete artifact collection: {p}")
        data=json.loads(p.read_text(encoding="utf-8"))
        assert data["status"]=="COMPLETE" and data["seed"]==seed
        case=data[key]
        assert len(case)==ncase
        selected={}
        for item in case:
            label=item.get("case",item.get("method"))
            assert label not in selected
            assert item["seed"]==seed
            assert item.get("budget",item.get("distinct_evaluation_budget"))==(20000 if name=="factorial" else 100000)
            seq=item["best_sequence"]
            digest=hashlib.sha256(("\n".join(seq)+"\n").encode()).hexdigest()
            assert digest==item["sequence_sha256"]
            value=float(item.get("final_loss_hr",item.get("search_best_loss_hr")))
            assert np.isfinite(value)
            assert item.get("expensive_calls",item.get("distinct_evaluations"))==(20000 if name=="factorial" else 100000)
            selected[label]=item
        values[int(seed)]=selected
    labels=[set(v) for v in values.values()]
    assert all(s==labels[0] for s in labels)
    return values

def paired_ci(d,nfamily=1):
    d=np.asarray(d,dtype=np.float64)
    n=len(d);avg=float(d.mean());sd=float(d.std(ddof=1))
    half=float(student_t.ppf(1-.05/(2*nfamily),n-1)*sd/np.sqrt(n))
    return dict(n=n,mean_delta_hr=avg,sd_delta_hr=sd,
                simultaneous95_low_hr=avg-half,simultaneous95_high_hr=avg+half,
                win_fraction=float(np.mean(d< -1e-10)),
                loss_fraction=float(np.mean(d> 1e-10)),
                median_delta_hr=float(np.median(d)),ci_family_size=nfamily)

def compare(data,reference,targets,name,field,nfamily=None):
    seeds=sorted(data)
    assert all(reference in data[s] for s in seeds)
    family=nfamily or len(targets)
    ans=[]
    for target in targets:
        diff=[float(data[s][target][field])-float(data[s][reference][field]) for s in seeds]
        row=paired_ci(diff,family)
        row.update(dataset=name,reference=reference,variant=target,
                   variant_mean_hr=float(np.mean([data[s][target][field] for s in seeds])),
                   baseline_mean_hr=float(np.mean([data[s][reference][field] for s in seeds])))
        ans.append(row)
    return ans

def factorial_effects(data):
    # Full balanced 2x2x2x2 only; the three no-prior controls are analyzed separately.
    seeds=sorted(data)
    effects=[]
    signs={}
    for p in (50,100):
        for k in (3,5):
            for m in (10,20):
                for n in ("none","quarter"):
                    name=f"p{p}_k{k}_m{m}_n{n}"
                    signs[name]={
                        "population":1 if p==100 else -1,
                        "tournament":1 if k==5 else -1,
                        "mutation":1 if m==20 else -1,
                        "neighbors":1 if n=="quarter" else -1,
                    }
    assert len(signs)==16
    factors=list(next(iter(signs.values())))
    terms=factors+["×".join([a,b]) for i,a in enumerate(factors) for b in factors[i+1:]]
    for term in terms:
        parts=term.split("×")
        contrast=[]
        for seed in seeds:
            # If y = intercept + beta_i*x_i + beta_ij*x_i*x_j,
            # main factor difference = 2*beta_i and diff-in-diffs = 4*beta_ij.
            scale=2 if len(parts)==1 else 4
            v=sum(float(data[seed][name]["final_loss_hr"])*
                  np.prod([signs[name][p] for p in parts])
                  for name in signs)/16*scale
            contrast.append(v)
        row=paired_ci(contrast,len(terms))
        row.update(factor_term=term,contrast_definition="main(high-low)" if len(parts)==1 else "difference-in-differences")
        effects.append(row)
    return effects

def alternative_summary(data):
    out=[]
    seeds=sorted(data)
    for name in ("ga_baseline","iterated_local","annealed_local"):
        rows=[data[s][name] for s in seeds]
        vals=np.array([r["search_best_loss_hr"] for r in rows])
        out.append(dict(method=name,seed_count=len(rows),
               mean_loss_hr=float(vals.mean()),median_loss_hr=float(np.median(vals)),
               sd_loss_hr=float(vals.std(ddof=1)),best_loss_hr=float(vals.min()),
               failure_to_beat_impact_fraction=float(np.mean(vals>=IMPACT_FIRST-1e-10)),
               mean_attempts=float(np.mean([r["attempted_evaluations"] for r in rows])),
               mean_wall_seconds=float(np.mean([r["elapsed_wall_seconds"] for r in rows]))))
    return out

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--allow-partial",action="store_true",
        help="Reserved: partial results must not be called complete.")
    a=parser.parse_args()
    assert not a.allow_partial, "Partial evidence requires separate explicitly labeled report"
    pilot=records("factorial");confirm=records("factorial_confirm_100k");alts=records("alternative")
    pbase="p100_k3_m10_nquarter"
    ptargets=sorted(set(next(iter(pilot.values())))-{pbase})
    ctargets=sorted(set(next(iter(confirm.values())))-{pbase})
    pilot_effects=compare(pilot,pbase,ptargets,"factorial_20k","final_loss_hr")
    confirm_effects=compare(confirm,pbase,ctargets,"factorial_confirm_100k","final_loss_hr")
    alt_effects=compare(alts,"ga_baseline",["iterated_local","annealed_local"],
                         "alternative_100k","search_best_loss_hr")
    record=dict(status="COMPLETE_RECONCILED",pilot_cells=len(pilot)*len(next(iter(pilot.values()))),
        confirm_cells=len(confirm)*len(next(iter(confirm.values()))),
        alternative_cells=len(alts)*len(next(iter(alts.values()))),
        per_seed_pair_effects=pilot_effects+confirm_effects+alt_effects,
        factorial_interactions=factorial_effects(pilot),
        alternative_method_summary=alternative_summary(alts),
        no_new_physical_samples=True,formal_policy_unchanged=True,
        statistical_scope="GA-seed stochasticity conditional on reused 64 training realizations; not physical validation")
    dest=ROOT/"DEEPER_METHOD_EVIDENCE.json"
    dest.write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    md=["# Follow-up GA interactions and alternative optimizers","","Three distinct jobs, separate common-seed blocks. GA training objective uses the original 64 physical planning inputs.","",
         "**Not a global-optimum proof. Not new independent physical validation.**",""]
    md+=["## GA factor interactions: 20k screening","",
         "| Term | Mean conditional effect (h) | Familywise 95% interval (h) |",
         "|---|---:|---:|"]
    for r in record["factorial_interactions"]:
        md.append(f"| {r['factor_term']} | {r['mean_delta_hr']:+.6f} | [{r['simultaneous95_low_hr']:+.6f}, {r['simultaneous95_high_hr']:+.6f}] |")
    md+=["","## GA vs non-GA: 100k exact distinct scores per method","",
         "| Method | 20-seed mean loss (h) | SD (h) | Min (h) | Attempted calls | Mean wall seconds |",
         "|---|---:|---:|---:|---:|---:|"]
    for r in record["alternative_method_summary"]:
        md.append(f"| {r['method']} | {r['mean_loss_hr']:.6f} | {r['sd_loss_hr']:.6f} | {r['best_loss_hr']:.6f} | {r['mean_attempts']:.0f} | {r['mean_wall_seconds']:.1f} |")
    md+=["","### Paired comparator effects versus GA","",
         "| Comparator | Mean (comparator − GA), h | Simultaneous 95% interval, h |",
         "|---|---:|---:|"]
    for r in alt_effects:
        md.append(f"| {r['variant']} | {r['mean_delta_hr']:+.6f} | [{r['simultaneous95_low_hr']:+.6f}, {r['simultaneous95_high_hr']:+.6f}] |")
    md+=["","## Confirmed 100k GA interaction and provenance controls","",
         "| Case | Mean difference versus final GA (h) | Familywise 95% interval (h) |",
         "|---|---:|---:|"]
    for r in confirm_effects:
        md.append(f"| {r['variant']} | {r['mean_delta_hr']:+.6f} | [{r['simultaneous95_low_hr']:+.6f}, {r['simultaneous95_high_hr']:+.6f}] |")
    md+=["","Intervals are descriptive across optimizer random seeds, with Bonferroni multiplicity by contrast family. The first-stage 12-seed factorial and 20-seed confirmation use *different* GA seeds. Algorithms have identical distinct-evaluation budgets; attempted queries, CPU/hardware, and initialization mechanisms can differ. No scientifically approved equivalence tolerance was set. Do not infer equality merely because an interval includes zero.",""]
    (ROOT/"DEEPER_METHOD_EVIDENCE.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    print("COMPLETE_METHOD_REPORT",dest,len(record["per_seed_pair_effects"]),flush=True)

if __name__=="__main__":
    main()
