"""Public discovery only; deliberately has no private/local production inputs."""
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

SOURCES = (
    'https://www.apra.gov.au/news-and-publications',
    'https://asic.gov.au/about-asic/news-centre/find-a-media-release/',
)
ALLOWED = {'www.apra.gov.au', 'apra.gov.au', 'asic.gov.au', 'www.asic.gov.au'}

class Links(HTMLParser):
    def __init__(self, base):
        super().__init__()
        self.base, self.links = base, set()

    def handle_starttag(self, tag, attrs):
        if tag != 'a':
            return
        href = dict(attrs).get('href', '')
        u = urljoin(self.base, href).split('#')[0]
        parsed = urlparse(u)
        news_path = ('/news-and-publications/' in parsed.path or
                     '/news-centre/find-a-media-release/' in parsed.path)
        if parsed.scheme == 'https' and parsed.hostname in ALLOWED and not parsed.query and news_path:
            self.links.add(u)

def collect(url):
    req = Request(url, headers={'User-Agent': 'HermesPublicSourceIndex/1.0'})
    with urlopen(req, timeout=25) as response:
        final = response.geturl()
        if urlparse(final).scheme != 'https' or urlparse(final).hostname not in ALLOWED:
            raise ValueError('Unexpected redirect destination')
        raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError('Source exceeds bounded capture')
        parser = Links(final)
        parser.feed(raw.decode('utf-8', errors='replace'))
        return {'url': url, 'final_url': final, 'bytes': len(raw),
                'sha256': hashlib.sha256(raw).hexdigest(),
                'links': sorted(parser.links)[:100], 'status': 'CAPTURED_INDEX_ONLY'}

def main():
    if os.environ.get('GITHUB_EVENT_NAME') != 'schedule':
        raise SystemExit('Only scheduled cloud execution is allowed')
    results = []
    for url in SOURCES:
        try:
            results.append(collect(url))
        except Exception as error:
            results.append({'url': url, 'status': 'SOURCE_FAILED',
                            'error_type': type(error).__name__})
    captured = sum(r['status'] == 'CAPTURED_INDEX_ONLY' for r in results)
    receipt = {'schema': 'hermes-public-cloud-source-receipt/v1',
               'observed_utc': datetime.now(timezone.utc).isoformat(),
               'github_event': 'schedule', 'github_run_id': os.environ['GITHUB_RUN_ID'],
               'runner_os': os.environ.get('RUNNER_OS'),
               'hermes_source_revision': os.environ['HERMES_SOURCE_REVISION'],
               'execution': 'native Hermes due script-only cron, not LLM inference',
               'captured_sources': captured, 'sources': results,
               'private_inputs': 0, 'account_writes': 0, 'model_calls': 0,
               'full_article_reads': 0}
    target = Path(os.environ['HERMES_HOME']) / 'public-cloud-receipt.json'
    data = (json.dumps(receipt, indent=2) + '\n').encode()
    target.write_bytes(data)
    assert target.read_bytes() == data
    print(data.decode())
    if not captured:
        raise SystemExit('No public source was captured')

if __name__ == '__main__':
    main()
