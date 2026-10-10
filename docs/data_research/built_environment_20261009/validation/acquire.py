"""Acquire authoritative validation sources; never touches pipeline outputs."""
from pathlib import Path
import argparse
import hashlib
import json
import requests
import zipfile
import io
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--phase', choices=['sources', 'wcs'], default='sources')
    args = p.parse_args()
    raw = ROOT / 'sources'
    raw.mkdir(exist_ok=True)
    urls = {
        'vre_directory.html': 'https://www2.census.gov/programs-surveys/acs/replicate_estimates/2022/data/5-year/140/',
        'B25024_06.csv.zip': 'https://www2.census.gov/programs-surveys/acs/replicate_estimates/2022/data/5-year/140/B25024_06.csv.zip',
        'B25034_06.csv.zip': 'https://www2.census.gov/programs-surveys/acs/replicate_estimates/2022/data/5-year/140/B25034_06.csv.zip',
        'VRE_2022_guide.pdf': 'https://www2.census.gov/programs-surveys/acs/replicate_estimates/2022/documentation/5-year/2018-2022_Variance_Replicate_Table_Documentation.pdf',
        'variance_tables.html': 'https://www.census.gov/programs-surveys/acs/data/variance-tables.html',
        'VRE_AVERAGE_WEIGHT_2022.csv': 'https://www2.census.gov/programs-surveys/acs/replicate_estimates/2022/documentation/5-year/VRE_AVERAGE_WEIGHT_2022.csv',
        'NLCD_guide_v1_1.pdf': 'https://www.mrlc.gov/sites/default/files/docs/LSDS-2103%20Annual%20National%20Land%20Cover%20Database%20%28NLCD%29%20Collection%201%20Science%20Product%20User%20Guide%20-v1.1%202025_06_11.pdf',
        'NLCD_guide_v1_0.pdf': 'https://www.mrlc.gov/sites/default/files/docs/LSDS-2103%20Annual%20National%20Land%20Cover%20Database%20%28NLCD%29%20Collection%201%20Science%20Product%20User%20Guide%20-v1.0%202024_10_15.pdf',
        'USGS_data_access.html': 'https://www.usgs.gov/centers/eros/science/data-access',
        'MRLC_services.html': 'https://www.mrlc.gov/data-services-page',
    }
    if args.phase == 'wcs':
        urls = {f'{product}_wcs.xml': f'https://dmsdata.cr.usgs.gov/geoserver/mrlc_{product}-Native_conus_year_data/wcs?service=WCS&request=GetCapabilities&version=2.0.1'
                for product in ['Fractional-Impervious-Surface', 'Land-Cover']}
    logpath = ROOT / 'ACQUISITION_LOG.json'
    log = json.loads(logpath.read_text()) if logpath.exists() else []
    for name, url in urls.items():
        dest = raw / name
        item = {'url': url, 'file': 'sources/' + name, 'accessed': '2026-10-09'}
        try:
            if dest.exists():
                data = dest.read_bytes()
                item['cached'] = True
            else:
                res = requests.get(url, timeout=(20, 180))
                item.update(http_status=res.status_code, content_type=res.headers.get('Content-Type'), resolved_url=res.url)
                res.raise_for_status()
                data = res.content
                dest.write_bytes(data)
            item.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            if name.endswith('.zip'):
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    item['members'] = z.namelist()
            print(json.dumps(item), flush=True)
        except Exception as e:
            item['error'] = str(e)
            print(json.dumps(item), flush=True)
        log.append(item)
        logpath.write_text(json.dumps(log, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
