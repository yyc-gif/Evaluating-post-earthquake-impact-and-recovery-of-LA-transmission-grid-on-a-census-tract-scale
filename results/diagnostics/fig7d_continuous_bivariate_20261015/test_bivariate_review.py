"""Scientific invariance and continuous-color regression tests."""
from common import *
from color_design import color,rgb_to_lab,srgb_to_linear,RGB_TO_XYZ,simulate
import fitz


def spec():return json.loads(lp(HERE/"COLOR_MAPPING_SPECIFICATION.json").read_text())


def test_frozen_population_and_eligibility():
    f,s=inputs()
    assert len(f)==2299 and len(s)==2315
    assert f.tract_id.is_unique and f.tract_id.str.fullmatch(r"\d{11}").all()
    assert f.Population.sum()==9066522 and (s.Population==0).sum()==16
    assert f.additional_zero_housing_positive_population.sum()==8


def test_exact_original_high_high_membership():
    f,_=inputs()
    hh=f.frozen_SOVI_quartile.eq("Q4")&f.MeanTotal5.ge(P75)
    old=pd.read_csv(lp(HERE/"inputs/ORIGINAL_94_GEOIDS.csv"),dtype={"tract_id":str})
    assert hh.sum()==94 and f.Population[hh].sum()==350799
    assert set(f.tract_id[hh])==set(old.tract_id)
    assert f.frozen_SOVI_quartile.eq("Q4").sum()==579
    assert f.MeanTotal5.ge(P75).sum()==575


def test_total_deficit_identity_and_no_threshold_recut():
    f,_=inputs()
    np.testing.assert_array_equal(f.MeanTotal5,f.B_Unconstrained+f.MeanDelta)
    assert P75==38.38135467381475
    assert abs(np.quantile(f.MeanTotal5,.75)-P75)<1e-12


def test_actual_continuous_values_no_classification_bins():
    s=spec()
    for design,info in s["designs"].items():
        scale=info["common_chroma_factors_at_257_burden_knots"]
        u=np.array([.41341,.41342,.41343]);v=np.array([.67121,.67122,.67123])
        a=color(u,np.full(3,.67),design,scale)
        b=color(np.full(3,.41),v,design,scale)
        assert np.unique(a,axis=0).shape[0]==3 and np.unique(b,axis=0).shape[0]==3


def test_equal_burden_equal_luminance_for_every_SOVI():
    s=spec();u,v=np.meshgrid(np.linspace(0,1,101),np.linspace(0,1,151))
    for design,info in s["designs"].items():
        rgb=color(u,v,design,info["common_chroma_factors_at_257_burden_knots"])
        L=rgb_to_lab(rgb)[...,0];Y=srgb_to_linear(rgb)@RGB_TO_XYZ[1]
        np.testing.assert_allclose(L,91-49*u,atol=1e-11,rtol=0)
        assert np.max(np.ptp(Y,axis=0))<1e-12
        assert (np.diff(L,axis=1)<0).all()


def test_no_clipping_on_dense_continuous_domain():
    s=spec();u,v=np.meshgrid(np.linspace(0,1,601),np.linspace(0,1,601))
    for design,info in s["designs"].items():
        rgb=color(u,v,design,info["common_chroma_factors_at_257_burden_knots"])
        assert rgb.min()>=0 and rgb.max()<=1 and np.isfinite(rgb).all()


def test_grayscale_limitation_is_disclosed_numerically():
    s=spec()
    for design,info in s["designs"].items():
        rgb=color(np.full(100,.5),np.linspace(0,1,100),design,info["common_chroma_factors_at_257_burden_knots"])
        gray=simulate(rgb,"grayscale")
        assert np.max(np.ptp(gray,axis=0))<1e-12


def test_A_C_unchanged_at_three_publication_resolutions():
    table=pd.read_csv(lp(HERE/"ABC_PIXEL_PRESERVATION.csv"))
    assert len(table)==6 and set(table.dpi)=={150,300,600}
    assert table.A_B_C_changed_color_channels.eq(0).all()


def test_vector_only_and_embedded_fonts():
    q=pd.read_csv(lp(HERE/"PDF_PUBLICATION_QA.csv"))
    assert q.raster_images.eq(0).all() and q.text_inside_page.all()
    assert (q.embedded_font_records>0).all()


def test_new_D_labels_and_sizing():
    d=fitz.open(lp(HERE/"FIGURE7_CONTINUOUS_REVIEW.pdf"))
    assert abs(d[0].rect.width/72-7.2)<1e-6 and d[0].rect.height/72==9
    text=" ".join(d[0].get_text().split())
    assert "High vulnerability & high recovery burden" in text
    assert "D. Recovery burden and social vulnerability" in text
    assert "SOVI quartile" not in text and "Q4 and deficit" not in text


def test_preservation_and_output_vector_proof():
    q=json.loads(lp(HERE/"INDEPENDENT_QA.json").read_text())
    assert q["status"]=="PASS" and q["full_vector_path_checks"]==2413
    assert q["protected_scientific_files"]==950
    assert q["publication_and_1021_worktrees_and_indexes_unchanged"]


def test_correct_K3_not_eight_variable_memberships():
    f,_=inputs()
    assert f.K3_class.value_counts().sort_index().tolist()==[1235,428,636]
    assert "FEMA_NCV14_CA_v119" not in f
