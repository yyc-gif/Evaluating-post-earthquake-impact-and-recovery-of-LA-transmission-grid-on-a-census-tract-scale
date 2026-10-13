"""Byte-check isolated layout regeneration; never invokes the suite builder."""
from pathlib import Path
import runpy
import sys

ROOT = Path(str(Path(__file__).resolve().parents[3]).removeprefix('\\\\?\\'))
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src/la_grid/plotting'))
import consolidate_current_figure_suite as u

names = [p.name for p in Path(u.lp(HERE)).iterdir() if p.is_file() and (
    p.name.startswith('FIGURE7_') and p.suffix in ['.pdf', '.png', '.csv']
    or p.name in ['PLOTTED_FROZEN_VALUES.csv', 'A_EMPIRICAL_DISTRIBUTION_POINTS.csv',
                 'NUMERICAL_STORY_QA.json', 'NA_FILL_COMPARISON_QA.json'])]
before = {name: u.sha(HERE / name) for name in names}
runpy.run_path(u.lp(HERE / 'build_layout_review.py'), run_name='__main__')
after = {name: u.sha(HERE / name) for name in names}
assert before == after, [name for name in names if before[name] != after[name]]
u.dump(HERE / 'ISOLATED_LAYOUT_REPRODUCTION_QA.json', {'all_declared_outputs_byte_identical': True,
    'checked_files': len(names), 'sha256': after, 'official_suite_builder_run': False,
    'scientific_fit_or_simulation_run': False})
print('Isolated layout reproduction PASS:', len(names), 'files byte-identical.')
