"""Independent source, distance, rank, payload and scientific-preservation QA."""
import csv
from decimal import Decimal
from importlib.metadata import version
import math
import py_compile
import zipfile

import fitz
from PIL import Image
from scipy.spatial.distance import cdist, pdist
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from threadpoolctl import threadpool_limits
from common import *


def independent_silhouette(dist, lab):
    classes = np.unique(lab)
    count = np.bincount(lab)
    means = np.stack([dist[:, lab == c].sum(1) / count[c] for c in classes], axis=1)
    own = means[np.arange(len(lab)), lab] * count[lab] / np.maximum(count[lab] - 1, 1)
    means[np.arange(len(lab)), lab] = np.inf
    other = means.min(1)
    result = (other - own) / np.maximum(own, other)
    result[count[lab] == 1] = 0
    return result


def main():
    s = source_reader()
    d = frame('VERIFIED_EIGHT_VARIABLE_COHORT.csv', 'tract_id')
    full = read(s, CB + 'FROZEN_P2_AND_COHORT.csv', 'tract_id')
    assert len(full) == 2315 and len(d) == 2299
    assert d.index.is_unique and d.index.str.fullmatch(r'\d{11}').all()
    assert set(d.index) == set(full.index[full.Population > 0])
    assert set(frame('EXCLUDED_ZERO_POPULATION_GEOIDS.csv', 'tract_id').index) == set(full.index[full.Population == 0])
    for col in ['Population', 'frozen_SOVI_quartile']:
        np.testing.assert_array_equal(d[col], full.loc[d.index, col])
    svi_serialization_error = np.max(np.abs(d.SOVI_SCORE - full.loc[d.index, 'SOVI_SCORE']))
    np.testing.assert_allclose(d.SOVI_SCORE, full.loc[d.index, 'SOVI_SCORE'], atol=2e-14, rtol=0)
    assert int(d.Population.sum()) == 9066522
    assert int(d.additional_zero_housing_positive_population.sum()) == 8
    assert np.isfinite(d[P2 + ['RPL_CBM']].to_numpy()).all()
    log_population_error = np.max(np.abs(np.log1p(d.Population) - d.log1p_Population))
    np.testing.assert_allclose(np.log1p(d.Population), d.log1p_Population, atol=4e-15, rtol=0)

    # Parse original national CSV with Decimal, not the analysis rank implementation.
    codes = ['NEHD', 'SMOKE', 'BURN', 'CFLD', 'DRGT', 'RFLD', 'HRCN', 'SWND', 'TRND']
    removals = {c: [c] for c in codes}
    removals.update(Heat=['NEHD'], Wildfire=['SMOKE', 'BURN'], Extreme_Events=['CFLD', 'DRGT', 'RFLD', 'HRCN', 'SWND', 'TRND'])
    original_sums, published, ids = [], [], []
    removed = {name: [] for name in removals}
    matched = {}
    total = 0
    sum_error = 0
    with zipfile.ZipFile(s.source(CB + 'sources/EJI_2024_United_States_CSV.zip', AUTH)) as z:
        with z.open('EJI_2024_United_States.csv') as file:
            rows = csv.DictReader(io.TextIOWrapper(file, encoding='utf-8-sig', newline=''))
            assert [c for c in codes if 'F_' + c not in rows.fieldnames] == ['NEHD', 'SMOKE', 'BURN']
            for row in rows:
                total += 1
                if row['GEOID'] in d.index:
                    matched[row['GEOID']] = row
                rank = float(row['RPL_CBM'])
                if not 0 <= rank <= 1:
                    continue
                decimal = [Decimal(row['EPL_' + c]) for c in codes]
                ticks = [int(v * 10000) for v in decimal]
                assert all(v >= 0 and Decimal(t) / 10000 == v for v, t in zip(decimal, ticks))
                original_sums.append(sum(ticks))
                published.append(rank)
                ids.append(row['GEOID'])
                sum_error = max(sum_error, abs(float(sum(decimal)) - float(row['SPL_CBM'])))
                for name, drop in removals.items():
                    removed[name].append(sum(t for c, t in zip(codes, ticks) if c not in drop))
    assert total == 85188 and len(ids) == 83509 and len(matched) == 2299 and sum_error < 1e-12
    published_expected = np.searchsorted(np.sort(original_sums), original_sums, side='left') / (len(ids) - 1)
    rounding_error = np.max(np.abs(published_expected - published))
    assert rounding_error <= .0000501
    saved_ranks = frame('ALL_COMPONENT_REMOVAL_NATIONAL_RANKS.csv', 'tract_id')
    max_rank_error = 0
    for name, values in removed.items():
        expected = np.searchsorted(np.sort(values), values, side='left') / (len(ids) - 1)
        expected = pd.Series(expected, index=ids).reindex(d.index)
        error = np.max(np.abs(expected - saved_ranks[name]))
        assert error < 1e-15
        max_rank_error = max(max_rank_error, error)
    for tract, row in matched.items():
        assert row['GEOID_2020'] == tract
        assert math.isclose(float(row['RPL_CBM']), d.loc[tract, 'RPL_CBM'], rel_tol=0, abs_tol=2e-16)
        assert int(row['F_HRCN']) == 1
    assert sum(float(v['E_BURN']) == 0 for v in matched.values()) == 2251
    print('QA: cohort and Decimal national/component ranks verified', flush=True)

    # Independently inspect the real official alternative workbook, never create or impute it.
    import openpyxl
    wb = openpyxl.load_workbook(lp(OUT / 'sources/EPA_PRISM_WORKBOOK.xlsx'), read_only=True, data_only=True)
    rows = iter(wb.active.iter_rows(values_only=True))
    columns = next(rows)
    pos = {name: i for i, name in enumerate(columns)}
    prism = {}
    for row in rows:
        tract = str(row[pos['TR_GEOID']]).removesuffix('.0').zfill(11)
        assert tract not in prism and len(tract) == 11
        hazard = float(row[pos['Hazard_Exp']])
        proportion = float(row[pos['Proport_Exp']])
        assert hazard == 1 + proportion
        prism[tract] = proportion
    wb.close()
    matched_prism = set(prism).intersection(d.index)
    absent_prism = set(d.index).difference(prism)
    assert len(prism) == 71798 and len(matched_prism) == 1879 and len(absent_prism) == 420
    assert int(d.loc[list(absent_prism), 'Population'].sum()) == 1392465
    join = frame('EPA_PRISM_2015_TO_FROZEN_2020_GEOID_AUDIT.csv', 'tract_id')
    assert set(join.index[join.identifier_match]) == matched_prism
    assert not join.same_geometry_verified.any()

    arrays = np.load(lp(OUT / 'REUSED_MAIN_FIT_ARRAYS.npz'))
    matrices = np.load(lp(OUT / 'REUSED_WEIGHTED_MATRICES.npz'))
    old_arrays = np.load(s.source(CK + 'REGISTERED_FIT_ARRAYS.npz', AUTH))
    old_matrices = np.load(s.source(CK + 'VERIFIED_WEIGHTED_MATRICES.npz', AUTH))
    for key in arrays.files:
        np.testing.assert_array_equal(arrays[key], old_arrays[key])
    for key in matrices.files:
        np.testing.assert_array_equal(matrices[key], old_matrices[key])
    np.testing.assert_array_equal(arrays['tract_ids'], d.index)
    assert len(arrays['keys']) == 492
    fit = frame('ALL_REGISTERED_K_AND_SEED_DIAGNOSTICS.csv').set_index(['specification', 'condition', 'k', 'seed'])
    con = frame('DOMAIN_AND_COORDINATE_CONTRIBUTIONS.csv')
    maximum_inertia_error, maximum_sil_error = 0, 0
    checked_silhouettes = 0
    cache = {}
    index = {key: i for i, key in enumerate(arrays['keys'])}
    for key, i in index.items():
        sp, rest = key.split('__', 1)
        condition = rest.rsplit('__k', 1)[0]
        k = int(key.rsplit('__k', 1)[1].split('__')[0])
        seed = int(key.rsplit('__s', 1)[1])
        x = matrices[sp + '__' + condition]
        lab = arrays['labels'][i]
        assert set(lab) == set(range(k))
        centers = np.stack([x[lab == c].mean(0) for c in range(k)])
        inertia = np.sum((x - centers[lab]) ** 2)
        error = abs(inertia - fit.loc[(sp, condition, k, seed), 'WCSS'])
        assert error < 1e-9
        maximum_inertia_error = max(maximum_inertia_error, error)
        if k > 1 and seed == 42:
            matrix_key = sp + '__' + condition
            if matrix_key not in cache:
                cache = {matrix_key: cdist(x, x, metric='euclidean')}
            error = np.max(np.abs(independent_silhouette(cache[matrix_key], lab) - arrays['silhouette'][i]))
            assert error < 1e-10
            maximum_sil_error = max(maximum_sil_error, error)
            checked_silhouettes += 1
        if condition == 'published':
            weights = np.array(BUDGETS[sp])
            np.testing.assert_array_equal(matrix(d, sp), x)
            assert abs(weights.sum() - 1) < 1e-15
            for a, b in [(0, 3), (3, 5), (5, len(weights))]:
                assert abs(weights[a:b].sum() - 1/3) < 1e-15
            if seed == 42:
                p = con.loc[con.specification.eq(sp) & con.condition.eq(condition) & con.k.eq(k) & con.seed.eq(seed)]
                assert abs(p.within_SS.sum() - inertia) < 1e-8
                assert abs(p.total_SS.sum() - 2299) < 1e-8

    # Every narrowly added component fit is verified in its saved, full-cohort space.
    new = np.load(lp(OUT / 'NEW_COMPONENT_FIT_ARRAYS.npz'))
    new_matrices = np.load(lp(OUT / 'NEW_COMPONENT_WEIGHTED_MATRICES.npz'))
    saved_centers = np.load(lp(OUT / 'NEW_COMPONENT_MODEL_CENTERS.npz'))
    component = frame('HAZARD_COMPONENT_SENSITIVITY.csv').set_index(['removed', 'k'])
    assert len(new['keys']) == 21
    maximum_final_center_gap = 0
    for i, key in enumerate(new['keys']):
        name = key.split('__remove_', 1)[1].split('__k')[0]
        k = int(key.rsplit('__k', 1)[1].split('__')[0])
        col = saved_ranks[name].to_numpy()
        expected = matrices['H2__published'].copy()
        expected[:, -1] = (col - col.mean()) / col.std() * np.sqrt(1/12)
        x = new_matrices[name]
        np.testing.assert_array_equal(x, expected)
        lab = new['labels'][i]
        centers = np.stack([x[lab == c].mean(0) for c in range(k)])
        centroid_wcss = np.sum((x - centers[lab]) ** 2)
        np.testing.assert_allclose(centroid_wcss, component.loc[(name, k), 'final_membership_centroid_WCSS'], atol=1e-9, rtol=0)
        returned_center_wcss = np.sum((x - saved_centers[key][lab]) ** 2)
        np.testing.assert_array_equal(cdist(x, saved_centers[key]).argmin(1), lab)
        error = abs(returned_center_wcss - component.loc[(name, k), 'WCSS'])
        assert error < 1e-9
        maximum_inertia_error = max(maximum_inertia_error, error)
        maximum_final_center_gap = max(maximum_final_center_gap, returned_center_wcss - centroid_wcss)
        independent = independent_silhouette(cdist(x, x), lab)
        error = np.max(np.abs(independent - new['silhouette'][i]))
        assert error < 1e-10
        maximum_sil_error = max(maximum_sil_error, error)
        baseline = arrays['labels'][index[f'H2__published__k{k}__s42']]
        assert abs(adjusted_rand_score(baseline, lab) - component.loc[(name, k), 'ARI']) < 1e-12
    repeated = KMeans(n_clusters=4, random_state=42, **PARAMS).fit(new_matrices['SMOKE']).labels_
    np.testing.assert_array_equal(repeated, new['labels'][list(new['keys']).index('H2__remove_SMOKE__k4__s42')])
    print('QA: all 492 reused and 21 new component fits verified', flush=True)

    info = frame('EIGHTH_COORDINATE_INCREMENTAL_INFORMATION.csv').set_index('variable')
    x = d[P2 + ['RPL_CBM']]
    for col in x:
        a = np.column_stack([np.ones(len(x)), x.drop(columns=col).to_numpy()])
        y = x[col].to_numpy()
        prediction = a @ np.linalg.lstsq(a, y, rcond=None)[0]
        r2 = 1 - np.sum((y - prediction) ** 2) / np.sum((y - y.mean()) ** 2)
        assert abs(r2 - info.loc[col, 'conditional_linear_R2']) < 1e-10
    zp = (d.log1p_Population - d.log1p_Population.mean()) / d.log1p_Population.std(ddof=0)
    zh = (d.RPL_CBM - d.RPL_CBM.mean()) / d.RPL_CBM.std(ddof=0)
    algebra_error = np.max(np.abs(pdist(matrices['P2__published'], 'sqeuclidean')
        + pdist(zh.to_numpy()[:, None], 'sqeuclidean') / 12
        - pdist(zp.to_numpy()[:, None], 'sqeuclidean') / 12
        - pdist(matrices['H2__published'], 'sqeuclidean')))
    assert algebra_error < 1e-11
    effective = json.loads(lp(OUT / 'EFFECTIVE_LOCAL_HAZARD_CONTENT.json').read_text())
    raw_components = np.array([[float(matched[t]['EPL_' + c]) for c in codes] for t in d.index])
    sums = raw_components.sum(1)
    shares = ((raw_components - raw_components.mean(0)) * (sums - sums.mean())[:, None]).mean(0) / sums.var()
    np.testing.assert_allclose(shares, list(effective['signed_indicator_covariance_shares'].values()), atol=1e-14)
    assert abs(shares.sum() - 1) < 1e-12

    # Raw acquisition responses include explicit failed/WAF responses, not fictional data.
    acquisition = json.loads(lp(OUT / 'OFFICIAL_SOURCE_ACQUISITION.json').read_text())
    for item in acquisition['records']:
        if 'archived_file' in item:
            path = OUT / 'sources' / item['archived_file']
            assert sha(path) == item['sha256'] and lp(path).stat().st_size == item['bytes']
    migrated = next(r for r in acquisition['records'] if r['name'] == 'NASA_NDH_MIGRATED_ZIP')
    assert migrated['http_status'] == 401 and migrated['status'] != 'ACQUIRED'
    assert 'urs.earthdata.nasa.gov' in migrated['final_url']
    links = json.loads(lp(OUT / 'NASA_NDH_OFFICIAL_DOWNLOAD_LINKS.json').read_text())['links']
    assert len(links) == 1 and all(v['rel'].endswith('/data#') for v in links)
    earlier = json.loads(lp(OUT / 'EARLIER_SOURCE_RESPONSE_ATTACHMENTS.json').read_text())['attachments']
    for item in earlier:
        assert sha(OUT / 'sources' / item['file']) == item['sha256']
        assert not item['original_complete_retrieval_record_available']

    start = json.loads(lp(OUT / 'STARTING_STATE_AND_PROTECTION.json').read_text())
    assert len(start['protected_files']) == 950
    for path, digest in start['protected_files'].items():
        assert sha(SOURCE_ROOT / path) == digest, path
    assert git('status', '--porcelain', cwd=SOURCE_ROOT).decode() == start['original_status']
    assert hashlib.sha256(git('diff', '--cached', '--binary', cwd=SOURCE_ROOT)).hexdigest() == start['original_staged_diff_sha256']
    assert prior_blobs() == start['prior_git_blobs']
    prefix = OUT.relative_to(ROOT).as_posix() + '/'
    assert all(p.startswith(prefix) for p in git('diff', '--name-only', AUTH).decode().splitlines())
    print('QA: 950 science payloads and original dirty/staged state preserved', flush=True)
    if git('rev-parse', 'HEAD').decode().strip() != AUTH:
        current = {}
        for line in git('ls-tree', '-r', 'HEAD', '--', 'docs/data_research').decode().splitlines():
            meta, path = line.split('\t', 1)
            if not path.startswith(prefix):
                current[path] = meta.split()[2]
        assert current == start['prior_git_blobs']

    graphics = []
    for path in sorted(lp(OUT / 'figures').glob('*.pdf')):
        doc = fitz.open(path)
        assert len(doc) == 1 and not doc[0].get_images()
        page = doc[0]
        text = page.get_text()
        assert 'EXPLORATORY EIGHT-VARIABLE AUTHOR REVIEW' in text and 'NOT FORMAL STAGE 7' in text
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                for span in line['spans']:
                    b = fitz.Rect(span['bbox'])
                    assert b.x0 >= -.5 and b.y0 >= -.5 and b.x1 <= page.rect.width + .5 and b.y1 <= page.rect.height + .5, (path.name, span)
        with Image.open(path.with_suffix('.png')) as im:
            assert min(im.info['dpi']) >= 599
            assert all(abs(a - b) <= 1 for a, b in zip(im.size, [round(page.rect.width/72*600), round(page.rect.height/72*600)]))
            pixels = im.size
        graphics.append(dict(file=path.name, pages=1, vector_without_image_objects=True, text_within_page=True,
            pixels=pixels, dpi=600, visual_review='Every final publication-size rendered page inspected in task'))
    assert len(graphics) == 7
    for script in lp(OUT).glob('*.py'):
        py_compile.compile(str(script), cfile=str(destination('tmp/' + script.stem + '.pyc')), doraise=True)
    qa = dict(review_status=WARN, status='PASS_NUMERICAL_AND_PRESERVATION_WITH_DISCLOSED_CDC_LIMITATIONS',
        authority=AUTH, candidate='H2-CBM eight-variable author review; no formal promotion',
        cohort=2299, full_service_domain=2315, excluded_zero_population=16, retained_zero_housing=8,
        national_valid=83509, independent_decimal_sum_error=sum_error, official_rounding_error=rounding_error,
        frozen_SOVI_CSV_serialization_max_error=svi_serialization_error, frozen_SOVI_comparison_tolerance=2e-14,
        stored_log_population_max_error=log_population_error, stored_log_population_comparison_tolerance=4e-15,
        exact_counterfactual_rank_max_error=max_rank_error, reused_fits_bitwise_identical=492,
        existing_full_cohort_silhouette_independently_verified_seed42=checked_silhouettes,
        new_component_fits_verified=21, one_component_deterministic_repeat=True,
        maximum_component_model_vs_final_centroid_WCSS_gap=maximum_final_center_gap,
        component_center_gap_reason='Registered tol=1e-4 can stop before returned centers equal final label means; both objectives saved, no parameter changes',
        maximum_independent_silhouette_error=maximum_sil_error, maximum_inertia_error=maximum_inertia_error,
        distance_algebra_max_error=algebra_error, EPA_PRISM_identifier_matches=1879,
        EPA_PRISM_unmatched=420, EPA_PRISM_unmatched_population=1392465,
        protected_files_unchanged=950, prior_diagnostic_git_blobs_unchanged=len(start['prior_git_blobs']),
        original_dirty_and_staged_state_unchanged=True, physical_models_rerun=False, formal_promotion=False,
        unresolved_original_physical_source_flags=True, clean_clone_full_physical_archive_verified=False,
        source_acquisition_payloads_verified=True, graphics=graphics,
        earlier_metadata_response_attachments_with_incomplete_attempt_history=len(earlier),
        versions={p: version(p) for p in ['numpy', 'pandas', 'scipy', 'scikit-learn', 'geopandas', 'matplotlib', 'PyMuPDF']})
    dump('INDEPENDENT_QA.json', qa)
    save('SOURCE_HASH_VERIFICATION_INDEPENDENT.csv', s.records)
    hashes = {}
    for path in sorted(lp(OUT).rglob('*')):
        rel = path.relative_to(lp(OUT)).as_posix()
        if path.is_file() and not any(v in rel.split('/') for v in ['tmp', '__pycache__']) and rel not in ['DERIVED_FILE_HASHES.json', 'REMOTE_DELIVERY_VERIFICATION.json']:
            hashes[rel] = dict(sha256=sha(path), bytes=path.stat().st_size)
    dump('DERIVED_FILE_HASHES.json', dict(review_status=WARN, files=hashes))
    print('INDEPENDENT QA PASS', json.dumps(clean({k: v for k, v in qa.items() if k not in ['graphics', 'versions']})), flush=True)


if __name__ == '__main__':
    with threadpool_limits(limits=1):
        main()
