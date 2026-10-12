from common import *
from collections import Counter
for key in ['Fig01','Fig03','Fig05','Fig07']:
    doc=fitz.open(lp(PKG/'before'/(key+'.pdf')))
    forms=[];colors=Counter()
    for x in streams(doc):
        raw=doc.xref_stream(x)
        if key=='Fig01' and len(raw)<1300:
            forms.append({'xref':x,'bbox':doc.xref_get_key(x,'BBox'),'raw':raw.decode('latin1')})
        for m in re.finditer(rb'([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+rg\b',raw):colors[tuple(float(v) for v in m.groups())]+=1
    dump('qa/'+key+'_probe.json',{'small_forms':forms,'colors':[[list(k),v] for k,v in colors.most_common()],
        'images':doc[0].get_images(),'shadings':[(x,doc.xref_object(x)) for x in range(1,doc.xref_length()) if doc.xref_get_key(x,'ShadingType')[0]!='null']})
    print(key,'forms',len(forms),'colors',len(colors),'images',doc[0].get_images())

