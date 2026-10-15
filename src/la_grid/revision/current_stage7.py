"""Read-only verifier for the sole adopted P2 Stage 7 authority."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd

FEATURES = ['Init_Supply','Grid_Impact','Redundancy_HHI','B_Unconstrained',
            'MeanDelta','SOVI_SCORE','log1p_Population']
BUDGETS = np.array([1/9,1/9,1/9,1/6,1/6,1/6,1/6])


def verify_current_stage7(root=None):
    root = Path(root) if root else Path(__file__).resolve().parents[3]
    pointer = json.loads((root/'config/current_stage7.json').read_text(encoding='utf-8'))
    assert pointer['version']=='2026-10-14' and pointer['fitted_feature_count']==7
    authority = root/pointer['authority']
    hashes = json.loads((authority/'ARTIFACT_HASHES.json').read_text(encoding='utf-8'))
    for name, expected in hashes.items():
        assert hashlib.sha256((authority/name).read_bytes()).hexdigest()==expected, name
    spec = json.loads((authority/'feature_schema_and_identity.json').read_text(encoding='utf-8'))
    assert spec['feature_names']==FEATURES and spec['primary_K']==3
    assert hashlib.sha256((authority/'feature_schema_and_identity.json').read_bytes()).hexdigest()==pointer['schema_sha256']
    arrays=np.load(authority/'preprocessing_and_labels.npz',allow_pickle=False)
    f=pd.read_csv(authority/'tract_features.csv',dtype={'tract_id':str},float_precision='round_trip')
    full=pd.read_csv(authority/'stage7_full_domain_tract_status.csv',dtype={'tract_id':str})
    assert len(f)==2299 and len(full)==2315 and f.Population.sum()==9066522
    assert f.tract_id.str.fullmatch(r'\d{11}').all() and f.tract_id.is_unique
    assert f.K3_class.value_counts().sort_index().tolist()==[1235,428,636]
    assert (full.Population==0).sum()==full.K3_class.isna().sum()==16
    assert f.additional_zero_housing_positive_population.sum()==8
    assert f.frozen_SOVI_quartile.eq('Q4').sum()==579
    np.testing.assert_array_equal(arrays['feature_names'],FEATURES)
    np.testing.assert_array_equal(arrays['tract_ids'],f.tract_id)
    np.testing.assert_array_equal(arrays['raw'],f[FEATURES])
    np.testing.assert_array_equal(arrays['K3_labels']+1,f.K3_class)
    np.testing.assert_allclose(arrays['budgets'],BUDGETS,atol=1e-16,rtol=0)
    np.testing.assert_allclose(f.MeanTotal5,f.B_Unconstrained+f.MeanDelta,atol=1e-12,rtol=0)
    return dict(status='PASS_SAVED_P2_REUSE',authority=pointer['authority'],eligible_tracts=2299,
        full_domain_tracts=2315,population=9066522,class_counts=[1235,428,636],fitted_feature_count=7,
        primary_K=3,sensitivity_K=4,artifact_count=len(hashes),no_new_fits_or_simulations=True)


def verify_current_figures(root=None):
    import csv
    import fitz
    root=Path(root) if root else Path(__file__).resolve().parents[3]
    checkpoint=json.loads((root/'docs/reproducibility/p2_final_adoption_20261014/BUILD_CHECKPOINT.json').read_text(encoding='utf-8'))
    assert checkpoint['model']=='P2' and checkpoint['fitted_feature_count']==7
    for name,h in checkpoint['output_hashes'].items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==h,name
    manifest=list(csv.DictReader((root/'results/figure_review/FIGURE_MANIFEST.csv').open(encoding='utf-8')))
    assert len(manifest)==32
    for row in manifest:
        assert hashlib.sha256((root/row['current_source_file']).read_bytes()).hexdigest()==row['sha256']
        assert hashlib.sha256((root/row['mirror_file']).read_bytes()).hexdigest()==row['sha256']
    with fitz.open(root/'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf') as packet:
        assert len(packet)==20
    return dict(status='PASS_CURRENT_P2_FIGURES',numbered_figures=16,packet_pages=20,
                mirrored_files=32,output_hashes_checked=len(checkpoint['output_hashes']),
                no_new_fits_or_simulations=True)


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1] not in ['--verify','--resume']:
        raise SystemExit('Use --verify or --resume; this command never fits a model.')
    print(json.dumps(verify_current_stage7(),indent=2))
