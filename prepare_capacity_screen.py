from pathlib import Path
import pandas as pd,json,hashlib
from r1_capacity_screen import screen_gna
r=Path.cwd();o=r/'Revision_Mapping_Gate';e=r/'External_Validation_Data';n=e/'normalized'
stations=pd.read_csv(r/'Data/working_area_substations_with_fragility.csv',dtype={'ID':str})
x=screen_gna(pd.read_csv(n/'SCE_GNA_Layer_5_Substation_Level_Planning_Assumptions.csv'),stations)
x.to_csv(o/'LOCAL_GNA_CAPACITY_SCREEN.csv',index=False)
h=pd.read_csv(r/'R1_Comment1_2_External_Evidence_20260922/SCE_REPRESENTED_HISTORICAL_LOAD.csv',dtype={'direct_id':str});h.to_csv(o/'HISTORICAL_LOAD_CONTEXT.csv',index=False)
ica=pd.read_csv(r/'R1_Comment1_2_External_Evidence_20260922/SCE_REPRESENTED_ICA_CAPACITY_CONTEXT.csv',dtype={'direct_July92_id':str});ica.to_csv(o/'ICA_HOSTING_CONTEXT.csv',index=False)
ladwp=[
 dict(July_ID='308581',facility='RS-Q Rack B',voltage='substation project; not assigned to abstract edge',quantity=160,unit='MVA',role='existing rating described2025',load=None,loading_ratio=None,source='ZEPEO_MND_2025.pdf',page=24),
 dict(July_ID='308581',facility='RS-Q proposed Rack D',voltage='project bank',quantity=160,unit='MVA',role='proposed addition; excluded from current network',load=None,loading_ratio=None,source='ZEPEO_MND_2025.pdf',page=24),
 dict(July_ID='307693',facility='Adelanto-Rinaldi Line1',voltage='500kV',quantity=1593,unit='A',role='existing line ampacity described2025; not station MW',load=None,loading_ratio=None,source='Adelanto_Rinaldi_MND_2025.pdf',page=9),
 dict(July_ID='307693',facility='Adelanto-Rinaldi Line1',voltage='500kV',quantity=1680,unit='A',role='proposed continuous rating; excluded from current network',load=None,loading_ratio=None,source='Adelanto_Rinaldi_MND_2025.pdf',page=9),
 dict(July_ID='307693',facility='Adelanto-Rinaldi Line1',voltage='500kV',quantity=1965,unit='A',role='proposed emergency rating; excluded from current network',load=None,loading_ratio=None,source='Adelanto_Rinaldi_MND_2025.pdf',page=9)]
pd.DataFrame(ladwp).to_csv(o/'LADWP_LOCAL_RATINGS_CONTEXT.csv',index=False)
now=x[x.year_value.eq(2026)]
summary={'matched_July_names':int(x.July_ID.nunique()),'named_voltage_facilities':int(x.facility.nunique()),'2026_rows':len(now),'2026_screenable':int(now.screenable.sum()),'2026_above_limit':now[now.above_planning_limit.fillna(False)][['July_ID','facility','loading_ratio','cumulative_demand','fac_load_limit','facility_loading','subst_capacity']].to_dict('records'),'new_generation_source_decisions':False,'network_limits_populated':False,'physical_interpretation':'Same-facility planning constraint context, not observed post-earthquake overload','ICA_interpretation':'hosting/integration capacity, not deliverable earthquake MW','LADWP_geometry_interpretation':'segment kW capacity bands not summed or assigned to stations','input_hashes':{str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [n/'SCE_GNA_Layer_5_Substation_Level_Planning_Assumptions.csv',r/'R1_Comment1_2_External_Evidence_20260922/SCE_REPRESENTED_HISTORICAL_LOAD.csv',r/'R1_Comment1_2_External_Evidence_20260922/SCE_REPRESENTED_ICA_CAPACITY_CONTEXT.csv',e/'raw/references/ZEPEO_MND_2025.pdf',e/'raw/references/Adelanto_Rinaldi_MND_2025.pdf']}}
(o/'CAPACITY_SCREEN_FINDINGS.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k!='input_hashes'},indent=2))
