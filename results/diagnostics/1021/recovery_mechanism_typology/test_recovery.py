"""Regression tests for the isolated recovery experiment, never formal Stage 7."""
import json
import numpy as np
import pandas as pd
from support import HERE, PRIOR, inputs, sha, snapshot
from analyze_recovery import preprocess


def test_frozen_identity_and_prior_preservation():
    a,f,_,_ = inputs()
    assert len(f)==2299 and f.Population.sum()==9066522
    assert f.additional_zero_housing_positive_population.sum()==8
    assert f.tract_id.str.fullmatch(r"\d{11}").all()
    assert snapshot()==json.loads((HERE/"FROZEN_INPUT_REGISTRY.json").read_text())["publication_snapshot"]


def test_protocol_precedes_experiments():
    run=json.loads((HERE/"ANALYSIS_RUN.json").read_text())
    assert run["protocol_commit"]=="bc7d7c0798588ac585426a59f98046f282df2383"
    assert run["protocol_sha256"]==sha(HERE/"PROTOCOL.md")
    assert run["new_resampling_fits"]==1125


def test_exact_temporal_integrals_and_initial_state():
    _,f,_,d=inputs()
    z=np.load(HERE/"RECOVERY_MATRICES.npz")
    np.testing.assert_array_equal(z["edges"],[0,6,24,72,168,480])
    np.testing.assert_allclose((1-z["A"])@np.diff(z["edges"]),d.impact__B480_mean,atol=1e-10)
    np.testing.assert_allclose(z["B"][:,0],f.Init_Supply,atol=1e-12)
    np.testing.assert_allclose(z["B"][:,1]+z["B"][:,2],d.impact__B480_mean,atol=1e-12)


def test_absolute_time_geometry_not_individual_normalization():
    src=np.load(HERE/"RECOVERY_MATRICES.npz")
    x,_=preprocess("A-full",src,np.arange(2299))
    np.testing.assert_allclose(x,src["A"]/np.sqrt(5),atol=0)
    assert src["A"][:,4].std()<1e-12


def test_pca_declared_variance_and_no_whitening():
    src=np.load(HERE/"RECOVERY_MATRICES.npz")
    x,desc=preprocess("A-PCA",src,np.arange(2299))
    assert desc["variance_ratio"].sum()>=.95
    assert desc["variance_ratio"][:-1].sum()<.95
    np.testing.assert_allclose(x,(src["A"]/np.sqrt(5)-desc["mean"])@desc["components"].T)


def test_mechanism_scaling_and_different_increment():
    src=np.load(HERE/"RECOVERY_MATRICES.npz")
    x,_=preprocess("B",src,np.arange(2299))
    np.testing.assert_allclose(x.std(0,ddof=0)**2,[1/3]*3,atol=1e-14)
    assert src["B_names"].tolist()==["initial_availability","baseline_deficit_hr","impact_increment_hr"]
    _,f,_,_=inputs()
    assert not np.allclose(src["B"][:,2],f.MeanDelta)


def test_all_fits_and_scenarios_present():
    d=pd.read_csv(HERE/"FULL_FIT_RESULTS.csv")
    assert len(d)==90
    assert set(d.k)==set(range(1,7)) and set(d.seed)==set(range(42,47))
    z=np.load(HERE/"ALL_FITTED_ARRAYS.npz")
    assert len(z["outcome_names"])==10
    assert not any("SOVI" in v or "Population" in v for v in z["outcome_names"])


def test_registered_draws_and_geography():
    d=pd.read_csv(HERE/"RESAMPLING_MEMBERSHIP.csv",dtype={"repeat":str})
    assert len(d[d.design=="random"])==900
    assert len(d[d.design=="spatial"])==225
    blocks=pd.read_csv(HERE/"CONTEXT_AND_SPATIAL_BLOCKS.csv").spatial_block
    assert blocks.nunique()==15
    assert set(d[d.design=="spatial"].repeat)==set(blocks)


def test_quartiles_and_special_tracts_preserved():
    c=pd.read_csv(HERE/"SOCIAL_AND_GEOGRAPHIC_CONTEXT.csv")
    assert (c.groupby(["representation","k"])["Q4_tracts"].sum()==579).all()
    assert (c.groupby(["representation","k"])["special_zero_housing_tracts"].sum()==8).all()
    assert (c.groupby(["representation","k"])["population"].sum()==9066522).all()


def test_independent_all_fit_checks():
    q=json.loads((HERE/"INDEPENDENT_QA.json").read_text())
    assert q["status"]=="PASS" and q["resampled_fit_geometry_checks"]==1125
    assert q["protected_scientific_files"]==950


def test_independent_continuous_and_simple_benchmarks():
    q=json.loads((HERE/"INDEPENDENT_QA.json").read_text())
    assert q["independent_benchmark_outcome_checks"]==11400


def test_exact_event_overlap_convention():
    from extract_features import widths
    t=np.array([0.,4.,11.,480.])
    np.testing.assert_array_equal(widths(t,2,6),[2,2,0])
    assert widths(t,0,480).sum()==480


def test_deterministic_registered_fit_reconstruction():
    from analyze_recovery import fit
    from threadpoolctl import threadpool_limits
    src=np.load(HERE/"RECOVERY_MATRICES.npz")
    z=np.load(HERE/"ALL_FITTED_ARRAYS.npz")
    with threadpool_limits(limits=1):
        for rep,k in [("A-full",2),("A-PCA",3),("B",3)]:
            x,_=preprocess(rep,src,np.arange(2299))
            model=fit(x,np.arange(2299),k,42)
            np.testing.assert_array_equal(model.labels_,z[f"{rep}_k{k}_s42_labels"])
            np.testing.assert_array_equal(model.cluster_centers_,z[f"{rep}_k{k}_s42_centers"])
