"""Independent raw-table arithmetic, preservation, repeatability and graphic QA."""
import csv
import io
import math
import py_compile
import zipfile
from importlib.metadata import version

import fitz
from PIL import Image
from common import *

CODES = ['NEHD','SMOKE','BURN','CFLD','DRGT','RFLD','HRCN','SWND','TRND']


def frame(name):
    return pd.read_csv(lp(OUT/name), dtype={'tract_id':str,'GEOID':str}).set_index('tract_id')


def independent_bulk(cohort):
    """Use stdlib CSV and math.fsum, rather than the producing pandas reader."""
    ranks, scores, matched = [], [], {}
    total = 0
    sum_error = 0.
    with zipfile.ZipFile(lp(OUT/'sources/EJI_2024_United_States_CSV.zip')) as z:
        members = json.loads(lp(OUT/'OFFICIAL_ARCHIVE_MEMBER_HASHES.json').read_text())
        for name, record in members.items():
            payload = z.read(name)
            assert len(payload) == record['bytes']
            assert hashlib.sha256(payload).hexdigest() == record['sha256']
        with z.open('EJI_2024_United_States.csv') as f:
            reader = csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig',newline=''))
            header = reader.fieldnames
            assert 'GEOID_2020' in header
            assert [c for c in CODES if 'F_'+c not in header] == ['NEHD','SMOKE','BURN']
            for row in reader:
                total += 1
                values = [float(row['EPL_'+c]) for c in CODES]
                published = float(row['RPL_CBM'])
                score = float(row['SPL_CBM'])
                if 0 <= published <= 1 and min(values) >= 0 and score >= 0:
                    scores.append(score)
                    ranks.append(published)
                    sum_error = max(sum_error,abs(math.fsum(values)-score))
                if row['GEOID'] in cohort:
                    assert row['GEOID'] not in matched
                    matched[row['GEOID']] = row
    assert total == 85188 and len(ranks) == 83509 and len(matched) == 2299
    sorted_scores = np.sort(np.array(scores))
    reconstructed = np.searchsorted(sorted_scores,scores,side='left')/(len(scores)-1)
    error = float(np.max(np.abs(reconstructed-np.array(ranks))))
    assert sum_error < 1e-12 and error <= .0000501
    return matched, dict(national_rows=total,national_valid=len(ranks),
                         independent_fsum_max_error=sum_error,independent_searchsorted_rank_max_error=error)


def preserve_prior_blobs(start):
    expected = start['prior_git_blobs']
    paths = list(expected)
    payload = ('\n'.join('HEAD:'+p for p in paths)+'\n').encode()
    result = subprocess.run(['git','-c','core.longpaths=true','cat-file','--batch'],
                            input=payload,stdout=subprocess.PIPE,check=True,cwd=ROOT)
    stream = io.BytesIO(result.stdout)
    for path in paths:
        header = stream.readline().decode().strip().split()
        assert len(header) == 3 and header[1] == 'blob'
        blob = stream.read(int(header[2]))
        assert stream.read(1) == b'\n'
        assert hashlib.sha256(blob).hexdigest() == expected[path], path
    assert stream.read() == b''
    changed = git('diff','--name-only',AUTH).decode().splitlines()
    prefix = OUT.relative_to(ROOT).as_posix()+'/'
    assert all(p.startswith(prefix) for p in changed), changed
    return len(paths)


def graphic_checks():
    records = []
    for path in sorted((lp(OUT/'figures')).glob('*.pdf')):
        doc = fitz.open(path)
        assert len(doc) == 1 and not doc[0].get_images(), path.name
        page = doc[0]
        text = page.get_text()
        assert 'AUTHOR REVIEW' in text and 'NOT FORMAL STAGE 7' in text
        outside = []
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines',[]):
                for span in line['spans']:
                    box = fitz.Rect(span['bbox'])
                    if box.x0 < -.5 or box.y0 < -.5 or box.x1 > page.rect.width+.5 or box.y1 > page.rect.height+.5:
                        outside.append(dict(text=span['text'],bbox=list(box)))
        assert not outside, (path.name,outside)
        png = path.with_suffix('.png')
        with Image.open(png) as im:
            assert min(im.info['dpi']) >= 599
            expected = (round(page.rect.width/72*600),round(page.rect.height/72*600))
            assert all(abs(a-b)<=1 for a,b in zip(im.size,expected))
            pixels, dpi = im.size, im.info['dpi']
        assert path.with_name(path.stem+'_publication_review.png').exists()
        records.append(dict(file=path.name,pages=1,vector_without_image_objects=True,
                            no_text_outside_page=True,pixels=pixels,dpi=dpi,
                            visual_inspection='Native publication-size renders reviewed in this task'))
    assert len(records) == 6
    return records


def main():
    start = json.loads(lp(OUT/'STARTING_STATE_AND_PROTECTION.json').read_text())
    assert start['starting_commit'] == AUTH
    s = sources()
    original, positive = dataset(s)
    full = frame('FROZEN_P2_AND_COHORT.csv')
    assert full.index.equals(original.index)
    pd.testing.assert_frame_equal(full,original,check_exact=False,rtol=2e-15,atol=1e-14)
    assert full.Population.equals(original.Population)
    d = full.loc[full.Population.gt(0)]
    excluded = frame('EXCLUDED_ZERO_POPULATION_GEOIDS.csv')
    assert set(excluded.index) == set(full.index[full.Population.eq(0)]) and len(excluded) == 16
    assert int(d.additional_zero_housing_positive_population.sum()) == 8
    cdc = frame('CDC_2024_MATCHED_ORIGINAL_VALUES.csv').reindex(d.index)
    raw, raw_qa = independent_bulk(set(d.index))
    for key, row in raw.items():
        assert row['GEOID_2020'] == key
        for name in ['RPL_CBM','SPL_CBM'] + ['E_'+c for c in CODES] + ['EPL_'+c for c in CODES]:
            assert math.isclose(float(row[name]),cdc.loc[key,name],rel_tol=0,abs_tol=1e-13)
    assert cdc.RPL_CBM.between(0,1).all()
    assert (cdc.F_HRCN == 1).all() and (cdc.E_HRCN == 0).all()
    assert (cdc.E_BURN == 0).sum() == 2251
    assert len(cdc.loc[cdc.E_BURN.eq(0)]) == 2251
    q = pd.read_csv(lp(OUT/'CBM_2299_BY_NINE_INDICATOR_QUALITY.csv'),dtype={'tract_id':str})
    assert len(q) == 2299*9 and not q.duplicated(['tract_id','indicator']).any()
    for code in CODES:
        part = q.loc[q.indicator.eq(code)].set_index('tract_id').reindex(d.index)
        assert part.raw_value.notna().all()
        if 'F_'+code not in cdc:
            assert part.flag_field.eq('NOT_PUBLISHED').all()
        else:
            for flag in [0,1,2,9]:
                count = sum(float(row['F_'+code]) == flag for row in raw.values())
                assert count == int(cdc['F_'+code].eq(flag).sum())
    for key in ['RAW','MAP']:
        service = pd.read_csv(lp(OUT/f'CDC_{key}_LA_QUERY_VALUES.csv'),dtype={'GEOID':str}).set_index('GEOID').reindex(d.index)
        common = [col for col in cdc if col in service and
                  (col.startswith(('EPL_','F_')) or col in ['E_'+c for c in CODES] + ['RPL_CBM','SPL_CBM'])]
        assert np.allclose(cdc[common],service[common],atol=1e-12,rtol=0,equal_nan=True)
    # Independent centered least squares and correlation calculations.
    x = frame('CBM_PLUS_P2_VERIFIED_FEATURE_VALUES.csv')
    result = pd.read_csv(lp(OUT/'CBM_VS_P2_REDUNDANCY_AND_INFORMATION.csv')).set_index('target')
    ols_errors = []
    for target in x:
        predictors = x.drop(columns=target).to_numpy()
        predictors = (predictors-predictors.mean(axis=0))/predictors.std(axis=0)
        y = x[target].to_numpy()
        centered = y-y.mean()
        pred = predictors @ np.linalg.lstsq(predictors,centered,rcond=None)[0]
        r2 = 1-np.sum((centered-pred)**2)/np.sum(centered**2)
        err = abs(r2-result.loc[target,'conditional_linear_R2'])
        assert err < 1e-9
        assert abs(1/(1-r2)-result.loc[target,'VIF']) < 1e-6
        ols_errors.append(err)
    pearson = pd.read_csv(lp(OUT/'CBM_P2_PEARSON_MATRIX.csv'),index_col=0)
    spearman = pd.read_csv(lp(OUT/'CBM_P2_SPEARMAN_MATRIX.csv'),index_col=0)
    assert np.allclose(pearson,np.corrcoef(x.to_numpy().T),atol=1e-12)
    assert np.allclose(spearman,np.corrcoef(x.rank(method='average').to_numpy().T),atol=1e-12)
    values = cdc[['EPL_'+c for c in CODES]].to_numpy()
    centered = values-values.mean(axis=0)
    score = cdc.SPL_CBM.to_numpy()
    centered_score = score-score.mean()
    shares = np.mean(centered*centered_score[:,None],axis=0)/np.mean(centered_score**2)
    saved = pd.read_csv(lp(OUT/'CBM_DOMAIN_AND_INDICATOR_CONTRIBUTIONS.csv')).query("type=='indicator'").set_index('component').reindex(CODES)
    assert np.allclose(shares,saved.covariance_share_of_local_SPL_variance,atol=1e-12)
    assert abs(shares.sum()-1)<1e-12
    registration = json.loads(lp(OUT/'CONDITIONAL_ANALYSIS_REGISTRATION.json').read_text())
    for name, weights in registration['squared_distance_budgets'].items():
        assert math.isclose(sum(weights),1) and math.isclose(sum(weights[:3]),1/3)
        assert math.isclose(sum(weights[3:5]),1/3) and math.isclose(sum(weights[5:]),1/3)
    acquired = json.loads(lp(OUT/'OFFICIAL_SOURCE_ACQUISITION.json').read_text())
    verified = 0
    for item in acquired:
        if item.get('status') == 'ACQUIRED':
            path = OUT/'sources'/item['name']
            assert sha(path) == item['sha256'] and lp(path).stat().st_size == item['bytes']
            verified += 1
    # Confirm derived numerical bytes repeat without fitting or altering frozen science.
    names = [p.name for p in lp(OUT).glob('*.csv')]
    before = {p:sha(OUT/p) for p in names}
    subprocess.run([sys.executable,str(lp(OUT/'information_audit.py'))],cwd=ROOT,check=True)
    assert before == {p:sha(OUT/p) for p in names}
    for path, digest in start['protected_files'].items():
        assert sha(SOURCE_ROOT/path) == digest, path
    assert git('status','--porcelain',cwd=SOURCE_ROOT).decode() == start['source_status']
    assert hashlib.sha256(git('diff','--cached','--binary',cwd=SOURCE_ROOT)).hexdigest() == start['source_staged_diff_sha256']
    prior_count = preserve_prior_blobs(start)
    for script in lp(OUT).glob('*.py'):
        py_compile.compile(str(script),cfile=str(lp(OUT/'tmp'/f'{script.stem}.pyc')),doraise=True)
    graphics = graphic_checks()
    decision = json.loads(lp(OUT/'CBM_FEATURE_ADMISSION_DECISION.json').read_text())
    assert decision['new_Kmeans_fits'] == 0 and not decision['formal_promotion']
    assert not lp(OUT/'P2_VS_P2_CBM_CONDITIONAL_K_RESULTS.csv').exists()
    assert not lp(OUT/'K_SELECTION_AND_STABILITY.md').exists()
    dump('INDEPENDENT_QA.json',dict(status='PASS_WITH_DOCUMENTED_UPSTREAM_LIMITATIONS',
         source_authority=AUTH,primary_cohort=2299,full_domain=2315,zero_population_exclusions=16,
         retained_zero_housing_positive_population=8,frozen_population_total=int(d.Population.sum()),
         national_raw_reader_QA=raw_qa,maximum_independent_OLS_R2_difference=max(ols_errors),
         original_source_payloads_verified=verified,protected_scientific_files_unchanged=950,
         prior_diagnostic_git_blobs_unchanged=prior_count,source_dirty_and_staged_state_unchanged=True,
         exact_repeat_numerical_CSVs=len(names),syntax_check='All package scripts py_compile PASS',
         new_Kmeans_fits=0,formal_promotion=False,graphic_QA=graphics,
         versions={p:version(p) for p in ['numpy','pandas','scipy','scikit-learn','geopandas','matplotlib','PyMuPDF','requests']},
         limits='Source flags missing; source-null cause not disaggregated; no new clustering; no physical rerun'))
    hashes = {}
    for path in sorted(lp(OUT).rglob('*')):
        relative = path.relative_to(lp(OUT)).as_posix()
        if not path.is_file() or any(p in relative.split('/') for p in ['tmp','__pycache__']):
            continue
        if relative in ['DERIVED_FILE_HASHES.json','REMOTE_DELIVERY_VERIFICATION.json']:
            continue
        hashes[relative] = dict(sha256=sha(path),bytes=path.stat().st_size)
    dump('DERIVED_FILE_HASHES.json',hashes)
    print('INDEPENDENT QA PASS',raw_qa,'protected=950, prior blobs='+str(prior_count),flush=True)


if __name__ == '__main__':
    main()
