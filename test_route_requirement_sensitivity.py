import numpy as np

from fragility_connectivity_audit import production_ds_probabilities
from route_requirement_sensitivity import gate_from_routes, thresholds


def test_fragility_shortcut_matches_nested_curves():
    ex, ds = production_ds_probabilities(np.array([.1]),
        np.array([[.15,.25,.35,.70]]), np.array([[.6,.5,.4,.4]]))
    np.testing.assert_allclose(ds[:,0]+ds[:,1],1-ex[:,1],atol=1e-15)


def test_fragility_cleanup_can_break_ds2_shortcut():
    ex, ds = production_ds_probabilities(np.array([.770516469750492]),
        np.array([[.09,.13,.17,.38]]),np.array([[.5,.4,.35,.35]]))
    assert ex[0,1]>ex[0,0]
    assert abs(ds[0,0]+ds[0,1]-(1-ex[0,1]))>1e-7


def test_local_source_survives_strict_route_requirements():
    f=np.array([[1.,.5,.5,0.]])
    F=np.array([[True,True,True,False]])
    route=np.array([[-1,1,3,0]])
    source=np.array([True,False,False,False])
    np.testing.assert_array_equal(gate_from_routes(f,F,route,source,1),[[1.,.5,.5,0.]])
    np.testing.assert_array_equal(gate_from_routes(f,F,route,source,2),[[1.,0.,.5,0.]])
    np.testing.assert_array_equal(gate_from_routes(f,F,route,source,3),[[1.,0.,.5,0.]])


def test_unreached_threshold_is_nan():
    result=thresholds(np.array([0.,100.,480.]),np.array([.1,.7,.79]))
    assert result['T50']==100.
    assert np.isnan(result['T80']) and result['T80_unreached']==1
