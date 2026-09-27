"""Read-only parity audit of the retained July substation fragility sampler."""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import lognorm

ROOT = Path(__file__).resolve().parent
HAZARDS = ("Northridge", "SanFernando", "LongBeach", "2pc50")


def production_ds_probabilities(pga, mu, beta):
    """Exact probability steps in C257H_Project_Main.sample_damage_states."""
    scales = np.clip(np.asarray(mu, float), 1e-6, None)
    dispersions = np.clip(np.asarray(beta, float), 1e-4, None)
    exceed = np.nan_to_num(lognorm.cdf(np.asarray(pga, float)[:, None],
                                       s=dispersions, scale=scales),
                           nan=0., posinf=1., neginf=0.)
    states = np.column_stack((1-exceed[:, 0], exceed[:, 0]-exceed[:, 1],
                              exceed[:, 1]-exceed[:, 2],
                              exceed[:, 2]-exceed[:, 3], exceed[:, 3]))
    states = np.clip(states, 0., 1.)
    sums = states.sum(axis=1, keepdims=True)
    sums[sums == 0.] = 1.
    states /= sums
    return exceed, states


def audit():
    formal = ROOT / "Formal_Experiment_20260923" / "Stage 1 Output_expanded"
    pga_table = pd.read_csv(ROOT / "Data/Substations_PGA_IDW_CEC_expanded.csv",
                            dtype={"ID": str}).set_index("ID")
    rows = []
    split_rows = []
    for hazard in HAZARDS:
        with np.load(formal / f"physical_inputs_{hazard}.npz", allow_pickle=False) as z:
            ids = z["station_ids"].astype(str)
        frame = pga_table.loc[ids]
        suffix = "" if hazard == "2pc50" else "_old"
        mu = frame[[f"mu_DS{i}{suffix}" for i in range(1, 5)]].to_numpy(float)
        beta = frame[[f"beta_DS{i}{suffix}" for i in range(1, 5)]].to_numpy(float)
        pga = frame[f"PGA_{hazard}"].to_numpy(float)
        exceed, ds = production_ds_probabilities(pga, mu, beta)
        old_mu = frame[[f"mu_DS{i}_old" for i in range(1, 5)]].to_numpy(float)
        old_beta = frame[[f"beta_DS{i}_old" for i in range(1, 5)]].to_numpy(float)
        now_mu = frame[[f"mu_DS{i}" for i in range(1, 5)]].to_numpy(float)
        now_beta = frame[[f"beta_DS{i}" for i in range(1, 5)]].to_numpy(float)
        _, ds_old = production_ds_probabilities(pga, old_mu, old_beta)
        _, ds_now = production_ds_probabilities(pga, now_mu, now_beta)
        full = ds[:, 0] + ds[:, 1]
        shortcut = 1-exceed[:, 1]
        for i, station in enumerate(ids):
            row = dict(hazard=hazard, station_id=station, pga_g=pga[i],
                       fragility_class=frame.iloc[i].fragility_class,
                       parameter_suffix=suffix or "current",
                       p_functional_full=full[i],
                       p_functional_shortcut=shortcut[i],
                       absolute_difference=abs(full[i]-shortcut[i]),
                       exceedances_nested=bool(np.all(np.diff(exceed[i]) <= 1e-14)),
                       production_cleanup_changed_shortcut=bool(abs(full[i]-shortcut[i]) > 1e-12))
            row.update({f"p_exceed_DS{j}": exceed[i,j-1] for j in range(1,5)})
            row.update({f"p_DS{j}": ds[i,j] for j in range(5)})
            rows.append(row)
            split_rows.append(dict(hazard=hazard,station_id=station,pga_g=pga[i],
                                   p_functional_old=float(ds_old[i,:2].sum()),
                                   p_functional_current=float(ds_now[i,:2].sum()),
                                   current_minus_old=float(ds_now[i,:2].sum()-ds_old[i,:2].sum()),
                                   production_parameter_set="current" if hazard=="2pc50" else "old"))
    result = pd.DataFrame(rows)
    if len(result) != 368:
        raise ValueError("Not all frozen station/hazard combinations were audited")
    result.to_csv(ROOT / "FRAGILITY_DS_PROBABILITY_PARITY.csv", index=False)
    pd.DataFrame(split_rows).to_csv(ROOT / "FRAGILITY_PARAMETER_SPLIT_DIAGNOSTIC.csv",index=False)
    return result


if __name__ == "__main__":
    a = audit()
    print(a.groupby("hazard").agg(max_difference=("absolute_difference", "max"),
                                   mean_difference=("absolute_difference", "mean"),
                                   non_nested=("exceedances_nested", lambda s: int((~s).sum())),
                                   cleanup_effect=("production_cleanup_changed_shortcut", "sum")).to_string())
