"""Contract and numerical tests of this isolated evidence package."""
import ast
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import audit

OUT=Path(__file__).resolve().parent


@pytest.fixture(scope='module')
def frame():
    return pd.read_csv(audit.longpath(OUT/'TRACT_CANDIDATE_VALUES_2315.csv'),dtype={'tract_id':str}).set_index('tract_id')


def test_ids_and_distinct_cohorts(frame):
    assert frame.index.str.fullmatch(r'06037\d{6}').all() and frame.index.is_unique
    assert len(frame)==2315 and frame.residential_member.sum()==2291
    assert frame.historical_CORE3_member.sum()==2287


def test_no_old_geometry_exclusion_in_primary(frame):
    regained=frame[frame.residential_member&~frame.historical_CORE3_member]
    assert set(regained.index)=={'06037189703','06037301601','06037301602','06037404600'}
    assert regained[audit.PRIMARY].notna().all().all()


def test_full_and_primary_completeness(frame):
    assert frame[audit.PRIMARY].notna().all().all()
    assert (frame.Population>=0).all()
    assert np.allclose(frame.log1p_Population,np.log1p(frame.Population))


def test_normalized_burden_identity(frame):
    assert frame.B_480_hr.between(0,480).all()
    assert frame.B_unconstrained.between(0,480).all()
    assert np.allclose(frame.Delta_B_logistics,frame.B_480_hr-frame.B_unconstrained,atol=1e-12)
    assert frame.Delta_B_logistics.min()>=-1e-12


def test_T80_censoring_is_not_horizon_fill(frame):
    assert not frame.T80_unreached.any()
    assert frame.T80.between(0,480,inclusive='left').all()
    assert frame.realization_terminal_below80_fraction.eq(0).all()


def test_SVI_source_comparison_reproduced():
    comparison=pd.read_csv(audit.longpath(OUT/'SVI_COMPOSITE_SOURCE_COMPARISON.csv'))
    assert comparison.previous_source_reproduced.all()
    frozen=comparison[comparison.measure_a=='frozen_Q'].set_index('measure_b')
    assert frozen.loc['CDC2022_RPL_THEMES','q4_overlap']==466
    assert frozen.loc['CDC2022_local_theme_mean','q4_overlap']==450


def test_source_bounds_and_missing_not_zero(frame):
    assert frame.SOVI_SCORE.between(0,100).all()
    assert frame.Redundancy_HHI.between(0,1).all()
    assert frame.Init_Supply.between(0,1).all()
    assert frame.CDC2022_RPL_THEMES.isna().sum()==24
    heating=frame.electric_heating_share.dropna()
    assert heating.between(0,1).all()


def test_same_cohort_matrices(frame):
    ids=pd.read_csv(audit.longpath(OUT/'PRIMARY_COHORT_GEOIDS.csv'),dtype=str).tract_id.tolist()
    for method in ['PEARSON','SPEARMAN']:
        matrix=pd.read_csv(audit.longpath(OUT/f'PRIMARY_2291_{method}.csv'),index_col=0)
        assert np.allclose(matrix,matrix.T,atol=1e-12)
        assert np.allclose(np.diag(matrix),1)
        assert np.allclose(matrix,frame.loc[ids,matrix.columns].corr(method=method.lower()),atol=1e-12)


def test_identity_block_VIF_not_treated_as_estimable():
    table=pd.read_csv(audit.longpath(OUT/'CONDITIONAL_EXPLAINED_VARIANCE_AND_VIF.csv'))
    identity=table[table.block=='RQ2_forbidden_identity_diagnostic_only']
    assert np.isinf(identity.VIF).all()
    assert np.allclose(identity.conditional_linear_R2,1,atol=1e-12)


def test_deterministic_tie_handling():
    s=pd.Series([1]*8,index=pd.Index([str(i).zfill(11) for i in reversed(range(8))],name='tract_id'))
    groups=audit.equal_quartiles(s)
    assert groups.loc['00000000000']=='Q1' and groups.loc['00000000007']=='Q4'


def test_no_clustering_import_or_weighted_fit():
    tree=ast.parse((OUT/'audit.py').read_text())
    modules=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
    assert not any('cluster' in (name or '') or 'decomposition' in (name or '') for name in modules)
    assert not any(isinstance(n,ast.Name) and n.id in {'KMeans','PCA','silhouette_score','adjusted_rand_score'} for n in ast.walk(tree))


def test_independent_archive_verification():
    record=json.loads((OUT/'INDEPENDENT_VERIFICATION.json').read_text())
    assert record['status']=='PASS' and record['all3000_payload_hashes_pass']


def test_protected_bytes_unchanged():
    assert json.loads((OUT/'PRESERVATION_BEFORE.json').read_text())==json.loads((OUT/'PRESERVATION_AFTER.json').read_text())


def test_candidate_register_primary_count_and_scope():
    register=pd.read_csv(audit.longpath(OUT/'THREE_RQ_CANDIDATE_REGISTER.csv'))
    primary=register[register.recommendation=='PRIMARY']
    assert set(primary.variable_name)==set(audit.PRIMARY)
    assert primary.valid_tract_count.eq(2291).all()
    assert primary.valid_full_domain_count.eq(2315).all()
    assert set(register.recommendation)=={'PRIMARY','CONDITIONAL','DESCRIPTIVE_ONLY','EXCLUDE'}


def test_population_source_uncertainty_is_not_hidden():
    qa=json.loads((OUT/'POPULATION_AND_DENSITY_SOURCE_QA.json').read_text())
    assert qa['frozen_population_matches_all_formal_rows']
    assert not qa['frozen_population_replaced']
    assert not qa['direct_upstream_population_release_resolved']
    assert qa['density_source_max_error']<1e-8


def test_heating_coverage_and_uncertainty(frame):
    heating=frame.loc[frame.residential_member]
    assert heating.electric_heating_share.notna().all()
    assert heating.electric_heating_share_moe90.notna().all()
    assert int((heating.electric_heating_share_moe90>.10).sum())==569
    assert heating.electric_heating_share_moe90.ge(0).all()


def test_hazard_and_policy_are_separate_fixed_references():
    h=json.loads((OUT/'HAZARD_SOURCE_QA.json').read_text())
    spec=json.loads((OUT/'AUDIT_SPECIFICATION.json').read_text())
    design=json.loads((OUT/'FROZEN_DESIGN_REFERENCE_QA.json').read_text())
    assert spec['hazard']=='2pc50' and spec['constrained_policy']=='impact-first'
    assert spec['unconstrained_policy']=='unconstrained'
    assert design['declared_production']['functional_threshold']==.5
    assert h['frozen_station_n']==92 and h['rows']==422176
    assert np.isclose(h['mean_return_interval_yr'],-50/np.log(.98))
