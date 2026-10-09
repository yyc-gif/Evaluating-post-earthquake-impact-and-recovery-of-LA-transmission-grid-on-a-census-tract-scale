"""Guard alignment and exact RNG-preserving search checkpoint behavior."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from la_grid.plotting.selected_strategy_artwork import right_aligned_feature_labels
from la_grid.revision.r1_ga_revision import run_revised_permutation_ga,RevisedGAConfig
from la_grid.diagnostics.extended_ga_search_20261008 import instrumented

def test_multiline_feature_labels_have_common_right_edge():
    fig,ax=plt.subplots(figsize=(5,3))
    ax.set_yticks(range(3))
    right_aligned_feature_labels(ax,['Recovery time','Population\ndensity','Social vulnerability score'])
    fig.canvas.draw();labels=ax.get_yticklabels()
    assert all(label.get_ha()=='right' and label._get_multialignment()=='right' for label in labels)
    right=np.array([label.get_window_extent().x1 for label in labels]);assert np.ptp(right)<.01
    plt.close(fig)

def test_checkpoint_resume_preserves_original_search_and_rng(tmp_path):
    items=tuple(str(i) for i in range(8));inc={'reference':items}
    def objective(order):
        x=np.array(list(map(int,order)));return -float(np.dot(np.arange(1,9),(x-np.array([4,2,7,0,6,1,3,5]))**2))
    path=tmp_path/'checkpoint.pkl.gz';records={}
    first=instrumented(path,records)(items=items,objective=objective,incumbents=inc,seed=47,config=RevisedGAConfig(20,150,.8,.2,3))
    resumed=instrumented(path,{})(items=items,objective=objective,incumbents=inc,seed=47,config=RevisedGAConfig(20,200,.8,.2,3))
    exact=run_revised_permutation_ga(items=items,objective=objective,incumbents=inc,seed=47,config=RevisedGAConfig(20,200,.8,.2,3))
    pd.testing.assert_frame_equal(first.history,exact.history.iloc[:151].reset_index(drop=True))
    pd.testing.assert_frame_equal(resumed.history,exact.history)
    assert resumed.best_sequence==exact.best_sequence and resumed.best_fitness==exact.best_fitness
