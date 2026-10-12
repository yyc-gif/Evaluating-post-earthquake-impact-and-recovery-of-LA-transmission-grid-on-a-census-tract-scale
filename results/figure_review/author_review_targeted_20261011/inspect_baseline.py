from common import *
import shutil

for directory in ['qa','before','alternatives']:(PKG/directory).mkdir(exist_ok=True)
records={}
for key in ['Main/Fig01','Main/Fig03','Main/Fig04','Main/Fig05','Main/Fig07','Supplement/FigS09']:
    doc,h=open_source('results/figure_review/'+key+'.pdf')
    short=key.split('/')[-1]
    preview(doc,'qa/'+short+'_before.png')
    raw=open(lp(source('results/figure_review/'+key+'.pdf')[0]),'rb').read()
    with open(lp(PKG/'before'/(short+'.pdf')),'wb') as f:f.write(raw)
    records[key]={'source_sha256':h,'size_mm':[doc[0].rect.width/MM,doc[0].rect.height/MM],
        'spans':spans(doc[0])}
    with open(lp(PKG/'qa'/(short+'_streams.txt')),'w',encoding='latin1') as f:
        for x in streams(doc):
            f.write(f'\n% XREF {x}\n'+doc.xref_stream(x).decode('latin1'))
dump('qa/BASELINE_INSPECTION.json',records)
prior=OUTER/'_le11/docs/data_research/built_environment_20261009/living_environment_audit_20261011/PRESERVATION_BEFORE.json'
old=json.load(open(lp(prior),encoding='utf-8'))
dump('qa/prior_preservation_schema.json',{'keys':list(old),'types':{k:type(v).__name__ for k,v in old.items()}})
print({k:{a:v[a] for a in ['source_sha256','size_mm']} for k,v in records.items()})
