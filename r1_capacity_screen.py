"""Evidence-bounded facility screening; no access to the production network."""
import re
import numpy as np
import pandas as pd

def normalized_site(value):
    return re.sub('[^A-Z0-9]','',re.sub(r'\s+\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)+(?:\s*kV)?(?:\s*System)?\s*$','',str(value),flags=re.I).upper())

def unique_station_crosswalk(stations):
    groups=stations[stations.Owner.eq('SCE')].groupby(stations.NAME.map(normalized_site))
    return {key:str(g.ID.iloc[0]) for key,g in groups if len(g)==1}

def screen_gna(records,stations):
    """Ratios require same facility/year and agreement with reported loading.

    Absolute native power unit is not established in the retained dictionary;
    report dimensionless ratio, not MW or MVA. Negative margins are legitimate.
    """
    x=records.copy(deep=True);lookup=unique_station_crosswalk(stations)
    x['July_ID']=x.substation_name.map(normalized_site).map(lookup)
    x=x[x.July_ID.notna()].copy()
    for field in ['cumulative_demand','fac_load_limit','facility_loading','subst_capacity']:
        x[field]=pd.to_numeric(x[field],errors='coerce')
        x.loc[x[field].eq(-9999),field]=np.nan
    numerical=x.cumulative_demand.ge(0)&x.fac_load_limit.gt(0)&np.isfinite(x.cumulative_demand)&np.isfinite(x.fac_load_limit)
    ratio=x.cumulative_demand/x.fac_load_limit
    error=abs(100*ratio-x.facility_loading)
    x['screenable']=numerical & error.le(.05)
    x['loading_ratio']=ratio.where(x.screenable)
    x['reported_loading_consistency_error_pp']=error.where(numerical)
    x['above_planning_limit']=pd.Series(pd.NA,index=x.index,dtype='boolean')
    x.loc[x.screenable,'above_planning_limit']=x.loc[x.screenable,'loading_ratio']>1
    x['margin_identity_error']=x.subst_capacity-(x.fac_load_limit-x.cumulative_demand)
    x['absolute_power_unit']='not established; no MW/MVA assumption'
    x['record_role']='planning forecast, not observed earthquake loading'
    x['facility_scope']='named voltage facility; not entire July transmission station'
    x['snapshot']='retained SCE GNA download20260922'
    return x
