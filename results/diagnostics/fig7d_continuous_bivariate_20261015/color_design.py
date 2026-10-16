"""Two bounded continuous CIELAB-D65 designs; no scientific-value binning."""
from common import *

WHITE=np.array([.3127/.3290,1.,(1-.3127-.3290)/.3290])
PRIMARIES=np.array([[.64/.33,.30/.60,.15/.06],[1.,1.,1.],
                    [(1-.64-.33)/.33,(1-.30-.60)/.60,(1-.15-.06)/.06]])
RGB_TO_XYZ=PRIMARIES@np.diag(np.linalg.solve(PRIMARIES,WHITE))
XYZ_TO_RGB=np.linalg.inv(RGB_TO_XYZ)
DESIGNS={"teal_wine":([-24.,-12.],[24.,12.]),
         "blue_amber":([-10.,-30.],[10.,30.])}
MACHADO={
    "protanopia":[[.152286,1.052583,-.204868],[.114503,.786281,.099216],[-.003882,-.048116,1.051998]],
    "deuteranopia":[[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]],
    "tritanopia":[[1.255528,-.076749,-.178779],[-.078411,.930809,.147602],[.004733,.691367,.303900]]}


def linear_to_srgb(v):
    return np.where(v<=.0031308,12.92*v,1.055*np.maximum(v,0)**(1/2.4)-.055)


def srgb_to_linear(v):
    return np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4)


def lab_to_linear(lab):
    L,a,b=np.moveaxis(np.asarray(lab),-1,0)
    fy=(L+16)/116
    f=np.stack([fy+a/500,fy,fy-b/200],axis=-1)
    xyz=np.where(f>6/29,f**3,3*(6/29)**2*(f-4/29))*WHITE
    return xyz@XYZ_TO_RGB.T


def rgb_to_lab(rgb):
    xyz=srgb_to_linear(np.asarray(rgb))@RGB_TO_XYZ.T/WHITE
    f=np.where(xyz>(6/29)**3,np.cbrt(xyz),xyz/(3*(6/29)**2)+4/29)
    return np.stack([116*f[...,1]-16,500*(f[...,0]-f[...,1]),200*(f[...,1]-f[...,2])],axis=-1)


def lab_field(u,v,design,scale):
    u,v=np.broadcast_arrays(u,v)
    low,high=np.array(DESIGNS[design])
    factor=np.interp(u,np.linspace(0,1,len(scale)),scale)
    ab=(low+(high-low)*v[...,None])*factor[...,None]
    return np.concatenate([(91-49*u)[...,None],ab],axis=-1)


def gamut_scale(design):
    # At each burden, one factor applies to the entire SOVI axis. Interpolation
    # makes this continuous and avoids a global pale-end gamut bottleneck.
    u,v=np.meshgrid(np.linspace(0,1,257),np.linspace(0,1,257))
    lo,hi=np.zeros(257),np.ones(257)
    for _ in range(36):
        mid=(lo+hi)/2
        rgb=lab_to_linear(lab_field(u,v,design,mid))
        allowed=(rgb.min(axis=(0,2))>=0)&(rgb.max(axis=(0,2))<=1)
        lo=np.where(allowed,mid,lo);hi=np.where(allowed,hi,mid)
    return .98*lo


def color(u,v,design,scale):
    u,v=np.broadcast_arrays(u,v)
    assert u.min()>=-1e-12 and u.max()<=1+1e-12
    assert v.min()>=0 and v.max()<=1
    linear=lab_to_linear(lab_field(u,v,design,scale))
    assert linear.min()>=0 and linear.max()<=1
    return linear_to_srgb(linear)


def simulate(rgb,mode):
    linear=srgb_to_linear(rgb)
    if mode=="grayscale":
        y=linear@RGB_TO_XYZ[1]
        return np.repeat(linear_to_srgb(y)[...,None],3,axis=-1)
    converted=linear@np.array(MACHADO[mode]).T
    # Display-only simulation gamut clipping, never clipping scientific variables.
    return linear_to_srgb(np.clip(converted,0,1))


def audit():
    f,_=inputs()
    r=f.MeanTotal5.to_numpy();s=f.SOVI_SCORE.to_numpy()
    lo,hi=float(r.min()),float(r.max())
    u=(r-lo)/(hi-lo);v=s/100
    specifications={"burden_normalization":{"minimum_hr":lo,"maximum_hr":hi,"rule":"u=(R-min)/(max-min); no clipping, nonlinear transform, percentile remap or rank bins"},
                    "SOVI_normalization":"v=SOVI_SCORE/100; original 0-100 scale, no recut quartiles",
                    "CIELAB_whitepoint":"D65","L_star":"91-49*u, identical for all vulnerability scores at common burden",
                    "gamut_rule":"At each burden, one common radial ab factor for the entire SOVI axis, 98% of maximum feasible factor. 257 gamut knots interpolated continuously; no RGB clipping for map colors",
                    "legend":"PDF function-based continuous shading with bilinear 16-bit sampled RGB function, not discrete data classes",
                    "designs":{},"CVD_method":"Machado et al.2009 severity100 matrices on linear sRGB; screen simulation, not clinical validation",
                    "CVD_matrices":MACHADO,"retrieval_date":"2026-10-15",
                    "references":["https://www.w3.org/Graphics/Color/srgb","https://www.w3.org/TR/css-color-4/",
                                   "https://doi.org/10.1109/TVCG.2009.113",
                                   "https://raw.githubusercontent.com/njsmith/colorspacious/master/colorspacious/cvd.py"]}
    rows=[];corners=[];display=f[["tract_id","Population","SOVI_SCORE","MeanTotal5","frozen_SOVI_quartile"]].copy()
    display["burden_u"]=u;display["vulnerability_v"]=v
    uu,vv=np.meshgrid(np.linspace(0,1,257),np.linspace(0,1,257))
    for design in DESIGNS:
        scale=gamut_scale(design)
        grid=color(uu,vv,design,scale);rgb=color(u,v,design,scale)
        recovered=rgb_to_lab(grid)
        y=srgb_to_linear(grid)@RGB_TO_XYZ[1]
        lerror=float(np.max(abs(recovered[...,0]-(91-49*uu))))
        assert lerror<1e-10 and np.max(np.ptp(y,axis=0))<1e-12
        for j,name in enumerate(["R","G","B"]):display[design+"_"+name]=rgb[:,j]
        specifications["designs"][design]={"ab_at_SOVI_0":list(DESIGNS[design][0]),"ab_at_SOVI_100":list(DESIGNS[design][1]),
            "common_chroma_factors_at_257_burden_knots":scale.tolist(),"gamut_grid_min_linear_RGB":float(lab_to_linear(lab_field(uu,vv,design,scale)).min()),
            "gamut_grid_max_linear_RGB":float(lab_to_linear(lab_field(uu,vv,design,scale)).max()),
            "cohort_colors_clipped":0,"equal_burden_max_luminance_spread":float(np.max(np.ptp(y,axis=0))),
            "L_star_roundtrip_max_error":lerror}
        for mode in ["normal","grayscale",*MACHADO]:
            actual=grid if mode=="normal" else simulate(grid,mode)
            lab=rgb_to_lab(actual)
            # Endpoint color distance at common burden: a descriptive audit, not a pass/fail psychophysical threshold.
            span=np.sqrt(((lab[-1]-lab[0])**2).sum(1))
            burden_span=np.sqrt(((lab[:,-1]-lab[:,0])**2).sum(1))
            rows.append({"design":design,"view":mode,"SOVI_endpoint_DeltaE76_min":span.min(),"SOVI_endpoint_DeltaE76_median":np.median(span),
                         "SOVI_endpoint_DeltaE76_max":span.max(),"burden_endpoint_DeltaE76_min":burden_span.min(),
                         "diagnostic_not_observer_validation":True})
        for ux in [0.,1.]:
            for vy in [0.,1.]:
                rr=color(np.array(ux),np.array(vy),design,scale)
                corners.append({"design":design,"burden_u":ux,"SOVI_score":100*vy,"R":rr[0],"G":rr[1],"B":rr[2]})
    save("TRACT_DISPLAY_COLORS.csv",display)
    save("PERCEPTUAL_ACCESSIBILITY_DIAGNOSTICS.csv",rows)
    save("PALETTE_CORNER_COLORS.csv",corners)
    dump("COLOR_MAPPING_SPECIFICATION.json",specifications)
    return specifications


if __name__=="__main__":audit()
