"""Called only by the scheduled workflow; never copies a production job store."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

def command(*args):
    result = subprocess.run(args, check=True, text=True, capture_output=True, timeout=120)
    print(result.stdout)
    return result.stdout

def main():
    assert os.environ.get('GITHUB_EVENT_NAME') == 'schedule', 'Schedule event required'
    assert os.environ.get('RUNNER_OS') == 'Linux', 'Standard Linux cloud runner required'
    home = Path(os.environ['HERMES_HOME'])
    home.mkdir(parents=True, exist_ok=True)
    scripts = home / 'scripts'
    scripts.mkdir(exist_ok=True)
    shutil.copyfile('scripts/public_source_index.py', scripts / 'public_source_index.py')
    text = command('hermes', 'cron', 'create', '1m', '--name',
                   'Cloud public source index', '--no-agent', '--script',
                   'public_source_index.py', '--repeat', '1', '--deliver', 'local')
    store = json.loads((home / 'cron/jobs.json').read_text())
    jobs = store['jobs'] if isinstance(store, dict) else store
    assert len(jobs) == 1 and jobs[0]['no_agent'] is True
    job_id = jobs[0]['id']
    print('NATIVE_HERMES_JOB', job_id)
    receipt = home / 'public-cloud-receipt.json'
    for _ in range(9):
        # Supported external scheduler tick, not cron run/forced execution.
        command('hermes', 'cron', 'tick')
        if receipt.exists():
            result = json.loads(receipt.read_text())
            assert result['github_run_id'] == os.environ['GITHUB_RUN_ID']
            assert result['captured_sources'] > 0
            command('hermes', 'cron', 'runs', job_id, '--limit', '1')
            print('VERIFIED_SCHEDULED_CLOUD_PROGRESS', json.dumps(result))
            return
        time.sleep(20)
    raise SystemExit('Native scheduled receipt did not arrive within the bounded window')

if __name__ == '__main__':
    main()
