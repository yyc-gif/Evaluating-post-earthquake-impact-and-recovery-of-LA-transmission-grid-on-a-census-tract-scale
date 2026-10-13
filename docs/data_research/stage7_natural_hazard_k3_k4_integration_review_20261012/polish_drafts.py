"""Typography only in newly generated review prose; no numerical or formal edits."""
import re
from common import *

def polish(text):
    text=re.sub(r'\b(all|the|The|of|for|contains|into|over|representing|with|from|about|than|only|retained|complete|has|approximately|have|additional|represents)(?=\d)',r'\1 ',text)
    text=re.sub(r'([A-Za-z])(?=(?:K[345]|RQ[123]|C[1234]|Q[1234])\b)',r'\1 ',text)
    text=re.sub(r'(?<=\d)(?=(?:tracts|residents|people|years|initializations)\b)',' ',text)
    text=re.sub(r'(?<=\d)h\b',' h',text)
    text=text.replace('run prepare.py,analyze.py,build_packet.py,figures.py and independent_qa.py','run prepare.py, analyze.py, build_packet.py, polish_drafts.py, figures.py and independent_qa.py; record_visual_qa.py is run only after actual rendered-page inspection')
    text=re.sub(r'\bARI\s*=?\s*(?=0\.)','ARI = ',text)
    for n in ['2299','2315','9066522','136453','350799']:
        text=re.sub(r'(?<![A-Za-z0-9_])'+n+r'(?![A-Za-z0-9_])',f'{int(n):,}',text)
    for a,b in [('andK4','and K4'),('cohort2299','cohort of 2,299'),('K3and','K3 and'),('SOVI quartiles','SOVI quartiles'),('the38','the 38'),('The38','The 38'),('and1000','and 1,000'),('one-third','one-third')]:text=text.replace(a,b)
    return text

if __name__=='__main__':
    names=['01_NATURAL_HAZARD_FINAL_DEFINITION_AND_EVIDENCE.md','02_K3_K4_FINAL_SCIENTIFIC_AUTHOR_DECISION.md','03_INTEGRATION_AUTHOR_APPROVAL_AND_PROMOTION_BOUNDARY.md','README.md']
    names += ['candidate/'+p.name for p in lp(OUT/'candidate').glob('*.md')]
    for name in names:
        p=lp(OUT/name);p.write_text(polish(p.read_text(encoding='utf-8')),encoding='utf-8',newline='\n')
