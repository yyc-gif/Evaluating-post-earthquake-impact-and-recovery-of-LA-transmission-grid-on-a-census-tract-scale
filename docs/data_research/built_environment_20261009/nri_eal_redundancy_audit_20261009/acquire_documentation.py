"""Acquire the exact v1.19 methodology; never replace the archived FEMA data."""
from pathlib import Path
import requests,hashlib,json
O=Path(__file__).resolve().parent
URL='https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf'
def main():
 p=O/'sources/FEMA_V119_TECHNICAL_DOCUMENTATION.pdf';expected=[x for x in json.loads((O/'DOCUMENT_ACQUISITION.json').read_text(encoding='utf-8')) if x['file']==p.name][0]['sha256']
 if p.exists():assert hashlib.sha256(p.read_bytes()).hexdigest()==expected;return
 r=requests.get(URL,timeout=(10,40));r.raise_for_status();assert r.content.startswith(b'%PDF') and hashlib.sha256(r.content).hexdigest()==expected,'Retrieved documentation differs from the verified March2023 document';p.parent.mkdir(exist_ok=True);p.write_bytes(r.content)
if __name__=='__main__':main()
