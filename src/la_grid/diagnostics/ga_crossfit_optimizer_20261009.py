"""Four-fold internal 64-sample planning cross-fit of cold-start GA vs ILS.

Each fold uses 48 training planning samples and 16 *internal* heldout planning
samples, five fresh optimizer seeds. Neither method uses the all-64 inherited
GA best: both get only seven deterministic heuristic sequences as references,
ILS begins with Impact-first, GA gets heuristic+uniform-random population.
No new physical realizations. Algorithm families/parameters were designed using
the full-64 problem previously, so this is *not an untouched external test*.
"""
from __future__ import annotations
import argparse,json
from dataclasses import replace
from pathlib import Path
import numpy as np

from la_grid.paths import REPO_ROOT
from la_grid.diagnostics.ga_init_param_20261009 import BASE,load
from la_grid.diagnostics.ga_alternative_optimizer_20261009 import local_search
from la_grid.diagnostics.ga_variant_engine import run_search
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.revision.r1_ga_exact_kernel import _mean_burden

OUT=REPO_ROOT/"results/diagnostics/ga_deeper_research_20261009"/"crossfit"
FOLD_SEED=19371
GA_SEEDS=(600,601,602,603,604)
BUDGET=50000
FOLDS=4

class KernelView:
    def __init__(self,kernel,selected):
        self.ids=kernel.ids
        self.index=kernel.index
        self.damage=np.ascontiguousarray(kernel.damage[selected])
        self.duration=np.ascontiguousarray(kernel.duration[selected])
        self.origin_index=kernel.origin_index
        self.base=kernel.base
        self.travel=kernel.travel
        self.neighbor_offset=kernel.neighbor_offset
        self.neighbors=kernel.neighbors
        self.source_flag=kernel.source_flag
        self.station_mass=kernel.station_mass
        self.total_mass=kernel.total_mass
        self.horizon=kernel.horizon
    def score(self,seq):
        seq=tuple(seq)
        assert len(seq)==92 and set(seq)==set(self.ids)
        order=np.array([self.index[v] for v in seq],dtype=np.int64)
        out=_mean_burden(order,self.damage,self.duration,self.origin_index,
              self.base,self.travel,self.neighbor_offset,self.neighbors,
              self.source_flag,self.station_mass,self.total_mass,self.horizon)
        assert np.isfinite(out)
        return -float(out)

def folds():
    order=np.random.default_rng(FOLD_SEED).permutation(64)
    groups=np.array_split(order,FOLDS)
    assert [len(g) for g in groups]==[16]*4
    assert set(np.concatenate(groups).tolist())==set(range(64))
    for i,g in enumerate(groups):
        held=np.sort(g)
        train=np.sort(np.setdiff1d(np.arange(64),held))
        yield i,train,held

def one(fold,seed):
    kernel,inc,quality,_=load()
    which={i:(tr,ho) for i,tr,ho in folds()}
    train_idx,held_idx=which[fold]
    train=KernelView(kernel,train_idx)
    held=KernelView(kernel,held_idx)
    assert train.damage.shape[0]==48 and held.damage.shape[0]==16
    assert abs(KernelView(kernel,np.arange(64)).score(inc["impact-first"])-kernel.score(inc["impact-first"]))<1e-8
    initial=tuple(inc["impact-first"])
    config=replace(BASE,initialization="legacy")  # excludes all prior-GA info
    ga=run_search(items=train.ids,incumbents=inc,objective=train.score,
        seed=seed,config=config,max_evaluations=BUDGET,
        checkpoints=(BUDGET,),folder=None,quality=initial)
    assert len(ga["cache"])==BUDGET and ga["state"]["expensive_calls"]==BUDGET
    ga_seq=ga["best_sequence"]
    ils=local_search(train,inc,initial,"iterated_local",seed,BUDGET)
    ils_seq=ils["best_sequence"]
    assert ils["completed_budget"] and ils["distinct_evaluations"]==BUDGET
    results=[]
    for method,seq,attempts in [
      ("cold_start_ga",ga_seq,int(ga["state"]["attempts"])),
      ("impact_start_ils",ils_seq,int(ils["attempted_evaluations"])),
      ("impact_reference",initial,0)
    ]:
        seq=list(seq)
        results.append(dict(
            method=method,fold=fold,seed=seed,budget=BUDGET,
            training_sample_count=48,holdout_sample_count=16,
            training_loss_hr=-train.score(seq),heldout_loss_hr=-held.score(seq),
            attempted_evaluations=attempts,
            best_sequence=seq,sequence_sha256=old.identity(seq),
            new_physical_samples=0,
            no_prior_best_injected=True))
    out=OUT/f"fold{fold}_seed{seed}"
    out.mkdir(parents=True,exist_ok=True)
    record=dict(status="COMPLETE",fold=fold,seed=seed,
        fold_split_seed=FOLD_SEED,train_indices=train_idx.tolist(),
        heldout_indices=held_idx.tolist(),run_results=results,
        training_procedure_selection_uses_holdout=False,
        methods_tuned_on_original_all64=True)
    (out/"RUN.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    print("CROSSFIT_RESULT",json.dumps(dict(
        fold=fold,seed=seed,
        ga_train=results[0]["training_loss_hr"],
        ils_train=results[1]["training_loss_hr"],
        ga_hold=results[0]["heldout_loss_hr"],
        ils_hold=results[1]["heldout_loss_hr"],
        reference_hold=results[2]["heldout_loss_hr"],
        ga_sha=results[0]["sequence_sha256"],
        ils_sha=results[1]["sequence_sha256"])),flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--fold",type=int,required=True)
    p.add_argument("--seed",type=int,required=True)
    a=p.parse_args()
    assert a.fold in range(FOLDS) and a.seed in GA_SEEDS
    one(a.fold,a.seed)

if __name__=="__main__":main()
