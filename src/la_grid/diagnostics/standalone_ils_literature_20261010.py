"""Record original DOI-agency bibliographic metadata without article copying."""
import requests
from la_grid.diagnostics.standalone_ils_20261010 import OUT, save


def main():
    rows = []
    for doi in ('10.1186/s40736-017-0032-5', '10.1049/iet-gtd.2017.0729',
                '10.1007/978-1-4419-1665-5_12', '10.1109/TPWRS.2019.2898966', '10.1002/eqe.623'):
        url = 'https://api.crossref.org/works/' + doi
        try:
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            m = r.json()['message']
            rows.append(dict(doi=doi, url=url, status='VERIFIED_ORIGINAL_DOI_AGENCY_METADATA',
                metadata={key: m.get(key) for key in ('DOI', 'title', 'author', 'container-title', 'publisher', 'volume', 'issue', 'page', 'article-number', 'published', 'published-print', 'published-online', 'URL')}))
        except requests.RequestException as e:
            rows.append(dict(doi=doi, url=url, status='FETCH_FAILED; see original publisher/author sources in literature table', error=type(e).__name__))
    save(OUT / 'LITERATURE_DOI_METADATA.json', rows)
    print([(r['doi'], r['status']) for r in rows])


if __name__ == '__main__':
    main()
