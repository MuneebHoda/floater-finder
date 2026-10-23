#!/usr/bin/env python3
"""Read official file metadata through the installed Kaggle client; never fetch WSIs."""
import argparse
import contextlib
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import tempfile
import time


def catalog(output, pause=2.):
    from kaggle.api.kaggle_api_extended import KaggleApi
    output = Path(output)
    if output.exists():
        raise FileExistsError('Choose a fresh catalog file')
    report = dict(competition='prostate-cancer-grade-assessment', complete=False,
                  source='authenticated official Kaggle file catalog', files=[], dataset_tiffs_downloaded=False)
    def checkpoint():
        report['updated_utc'] = datetime.now(timezone.utc).isoformat()
        temporary = output.with_suffix('.partial')
        temporary.write_text(json.dumps(report, indent=2)+'\n')
        temporary.replace(output)
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            api = KaggleApi()
            api.authenticate()
        cursor = None
        for page in range(120):
            for attempt in range(3):
                try:
                    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        result = api.competition_list_files(report['competition'], page_token=cursor, page_size=200)
                    break
                except Exception as error:
                    response = getattr(error, 'response', None)
                    if getattr(response, 'status_code', None) != 429 or attempt == 2:
                        raise
                    time.sleep(65)
            report['files'].extend(dict(name=f.name, bytes=f.total_bytes) for f in result.files)
            cursor = result.next_page_token
            checkpoint()
            if page % 10 == 0:
                print(json.dumps(dict(pages=page+1, files=len(report['files']))), flush=True)
            if not cursor:
                report['complete'] = True
                break
            time.sleep(pause)
        if not report['complete']:
            raise ValueError('Catalog exceeds 24000-file bound')
        # A small metadata-only download tests the selective-download/rules gate.
        with tempfile.TemporaryDirectory(prefix='panda-metadata-probe-') as tmp:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                api.competition_download_file(report['competition'], 'train.csv', path=tmp, quiet=True)
            paths = list(Path(tmp).iterdir())
            if len(paths) != 1 or paths[0].stat().st_size > 2_000_000:
                raise ValueError('Unexpected metadata probe output')
            report['metadata_probe'] = dict(name=paths[0].name, bytes=paths[0].stat().st_size,
                sha256=hashlib.sha256(paths[0].read_bytes()).hexdigest())
        checkpoint()
        print(json.dumps(dict(status='complete', path=str(output), files=len(report['files']))), flush=True)
        return 0
    except Exception as error:
        report['error'] = dict(type=type(error).__name__, http_status=getattr(getattr(error,'response',None),'status_code',None))
        checkpoint()
        print(json.dumps(dict(status='blocked', **report['error'])), flush=True)
        return 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    raise SystemExit(catalog(args.output))
