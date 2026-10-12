"""Independent stdlib-only reconstruction of archived S05 data, no model calls."""
from bisect import bisect_right
import csv
import hashlib
import io
import json
import os
from pathlib import Path
from statistics import mean, median
import unittest
import zipfile

OUT = Path(__file__).resolve().parent
if os.name == 'nt':
    OUT = Path('\\\\?\\' + str(OUT))
RUNS = 'initialization/results/diagnostics/ga_random_initialization_isolation_20261011/runs/PURE_RANDOM_GA_'
FINAL = 'final/results/diagnostics/pure_random_ga_final_20261011/'


def table(data):
    return list(csv.DictReader(io.StringIO(data.decode('utf-8'))))


class ArchivedS05(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = zipfile.ZipFile(OUT / 'SOURCE_EVIDENCE.zip')

    @classmethod
    def tearDownClass(cls):
        cls.archive.close()

    def test_exact_source_hashes_and_candidate(self):
        manifest = json.loads((OUT / 'SOURCE_DATA_PROVENANCE_MANIFEST.json').read_text(encoding='utf-8'))
        self.assertEqual(len(manifest['sources']), 86)
        for row in manifest['sources']:
            data = self.archive.read(row['archive_member'])
            self.assertEqual(hashlib.sha256(data).hexdigest(), row['sha256'])
            self.assertEqual(len(data), row['bytes'])
        candidate = json.loads(self.archive.read(FINAL + 'FINAL_RANDOM_GA_CANDIDATE.json'))
        self.assertEqual(len(set(candidate['sequence'])), 92)
        self.assertEqual(hashlib.sha256(('\n'.join(candidate['sequence'])+'\n').encode()).hexdigest(),
                         'edc4ad19f61a6d89d83532c1c92f353243b5d9e7b475c1ad99873227bbfeb99a')
        self.assertEqual(candidate['planning_objective_hr'], 32.99552241352315)

    def test_random_pools_endpoints_and_median_without_interpolation(self):
        seed_table = {int(r['seed']): r for r in table((OUT/'INITIAL_AND_FINAL_SEED_LOSSES.csv').read_bytes())}
        curves, union = [], {100, 100000}
        for seed in range(2026103100, 2026103120):
            receipt = json.loads(self.archive.read(RUNS + str(seed) + '/FINAL_100000.json'))
            pool = json.loads(self.archive.read(RUNS + str(seed) + '/INITIAL_POPULATION.json'))
            self.assertEqual(pool['initial_sequences'], pool['common_random_pool'])
            self.assertEqual(pool['archive_before_first_evaluation'], [])
            self.assertEqual(len({tuple(x) for x in pool['initial_sequences']}), 100)
            moves = json.loads(self.archive.read(RUNS + str(seed) + '/STRICT_IMPROVEMENTS.json'))
            moves = [x for x in moves if x['distinct_evaluations'] <= 100000]
            initial = [x for x in moves if x['generation'] == 0][-1]['service_loss_hr']
            self.assertEqual(initial, float(seed_table[seed]['initial_best_loss_hr']))
            self.assertEqual(moves[-1]['service_loss_hr'], receipt['loss_hr'])
            self.assertEqual(receipt['loss_hr'], float(seed_table[seed]['final_best_loss_hr']))
            self.assertEqual(receipt['distinct_evaluations'], 100000)
            x = [m['distinct_evaluations'] for m in moves]
            y = [m['service_loss_hr'] for m in moves]
            union.update(x)
            curves.append((x, y))
        grid = sorted(t for t in union if t >= 100)
        saved = table((OUT/'PANEL_A_MEDIAN_ARCHIVE.csv').read_bytes())
        self.assertEqual([int(row['distinct_evaluations']) for row in saved], grid)
        for row, t in zip(saved, grid):
            value = median(y[bisect_right(x, t)-1] for x, y in curves)
            self.assertAlmostEqual(value, float(row['median_best_observed_loss_hr']), places=12)

    def test_complete_pairing_saved_interval_and_exact_accounting(self):
        rows = table(self.archive.read(FINAL + 'REALIZATION_OUTCOMES.csv'))
        ga = {r['realization_id']: r for r in rows if r['strategy'] == 'GA-pure-random'}
        impact = {r['realization_id']: r for r in rows if r['strategy'] == 'Impact-first'}
        self.assertEqual(set(ga), set(impact))
        self.assertEqual(len(ga), 2000)
        self.assertEqual(len({r['physical_sha256'] for r in ga.values()}), 2000)
        plotted = {r['realization_id']: r for r in table((OUT/'PHYSICAL_PAIRED_DISTRIBUTION.csv').read_bytes())}
        self.assertEqual(set(ga), set(plotted))
        deltas, component_means = [], [[], [], []]
        components = ['L_self_population_mass_weighted_hr', 'L_threshold_population_mass_weighted_hr', 'L_source_population_mass_weighted_hr']
        key = 'population_weighted_normalized_burden_hr'
        for rid, a in ga.items():
            b = impact[rid]
            self.assertEqual(a['physical_sha256'], b['physical_sha256'])
            self.assertEqual(float(a['horizon_hr']), 480)
            self.assertEqual(float(b['horizon_hr']), 480)
            value = float(a[key])-float(b[key])
            deltas.append(value)
            self.assertAlmostEqual(value, float(plotted[rid]['GA_minus_Impact_loss_hr']), places=12)
            parts = [float(a[c])-float(b[c]) for c in components]
            self.assertAlmostEqual(sum(parts), value, places=10)
            for values, part in zip(component_means, parts):
                values.append(part)
        self.assertEqual(sum(v < 0 for v in deltas), 1741)
        self.assertEqual(sum(v > 0 for v in deltas), 259)
        effects = table(self.archive.read(FINAL + 'PAIRED_EFFECTS.csv'))
        primary = next(r for r in effects if r['candidate'] == 'GA-pure-random' and r['reference'] == 'Impact-first' and r['metric'] == key)
        self.assertAlmostEqual(mean(deltas), float(primary['mean_difference']), places=12)
        self.assertAlmostEqual(float(primary['simultaneous95_low']), -.56398203866016117, places=12)
        self.assertAlmostEqual(float(primary['simultaneous95_high']), -.50232131526136481, places=12)
        displayed = table((OUT/'POPULATION_LOSS_COMPONENTS.csv').read_bytes())
        for vals, row in zip(component_means, displayed):
            self.assertAlmostEqual(mean(vals), float(row['mean_difference_hr']), places=12)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ArchivedS05)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    (OUT/'ARCHIVED_RECONSTRUCTION_TEST_RESULTS.json').write_text(json.dumps(dict(
        status='PASS' if result.wasSuccessful() else 'FAIL', tests_run=result.testsRun,
        failures=len(result.failures), errors=len(result.errors),
        scope='Independent stdlib-only reconstruction; zero optimizer, physical, production or bootstrap calls'), indent=2)+'\n', encoding='utf-8', newline='\n')
    raise SystemExit(not result.wasSuccessful())
