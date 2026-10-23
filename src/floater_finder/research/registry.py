"""Append-only per-run registry with hash-verified resumable JSON checkpoints."""
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from .contracts import ExperimentRun, canonical, fingerprint


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.pending-', mode='w', delete=False) as handle:
        pending = Path(handle.name)
        try:
            handle.write(canonical(value)+'\n')
            handle.flush()
            os.fsync(handle.fileno())
        except BaseException:
            pending.unlink(missing_ok=True)
            raise
    try:
        os.link(pending, path)  # Exclusive install; never replaces an existing successful artifact.
    finally:
        pending.unlink(missing_ok=True)


class Registry:
    def __init__(self, root, run):
        if not isinstance(run, ExperimentRun):
            raise TypeError('Versioned ExperimentRun required')
        self.root, self.run = Path(root), run
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root/'events').mkdir(exist_ok=True)
        self.identity = fingerprint(asdict(run))
        self._cached_events = None
        self._cached_directory_mtime = None
        with self._lock():
            manifest = self.root/'run.json'
            if not manifest.exists():
                _atomic_new(manifest, dict(run=asdict(run), identity=self.identity))
            if json.loads(manifest.read_text()) != dict(run=asdict(run), identity=self.identity):
                raise ValueError('Run identity/configuration changed; choose a new output')
            self.events()

    @contextmanager
    def _lock(self):
        with (self.root/'.registry.lock').open('a') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def events(self):
        events, previous = [], self.identity
        for sequence, path in enumerate(sorted((self.root/'events').glob('*.json'))):
            row = json.loads(path.read_text())
            digest = row.pop('event_sha256')
            if (path.name != f'{sequence:06d}.json' or row['sequence'] != sequence or
                    row['previous_sha256'] != previous or fingerprint(row) != digest):
                raise ValueError('Registry event chain was changed or truncated')
            for artifact in row.get('artifacts', []):
                target = self.root/artifact['path']
                if self.root.resolve() not in target.resolve().parents or file_hash(target) != artifact['sha256']:
                    raise ValueError('Checkpoint artifact hash changed')
            row['event_sha256'] = digest
            previous = digest
            events.append(row)
        seal = self.root/'seal.json'
        if seal.exists() and json.loads(seal.read_text()) != dict(events=len(events), last_sha256=previous, run_identity=self.identity):
            raise ValueError('Sealed registry tail changed')
        self._cached_events = events
        self._cached_directory_mtime = (self.root/'events').stat().st_mtime_ns
        return events

    def _current_events(self):
        if self._cached_events is not None and self._cached_directory_mtime == (self.root/'events').stat().st_mtime_ns:
            return self._cached_events
        return self.events()

    def _append(self, kind, **values):
        events = self._current_events()
        row = dict(sequence=len(events), previous_sha256=events[-1]['event_sha256'] if events else self.identity,
                   kind=kind, timestamp_utc=datetime.now(timezone.utc).isoformat(), **values)
        row['event_sha256'] = fingerprint(row)
        _atomic_new(self.root/'events'/f'{len(events):06d}.json', row)
        self._cached_events = events + [row]
        self._cached_directory_mtime = (self.root/'events').stat().st_mtime_ns
        return row

    def status(self, status, *, validation=None, interpretation=None, limitations=(), slurm_job_id=None):
        if status not in ('planned', 'running', 'verified', 'failed', 'excluded'):
            raise ValueError('Known experiment status required')
        with self._lock():
            prior = [r['status'] for r in self._current_events() if r['kind'] == 'status']
            allowed = {None: ('planned',), 'planned': ('running', 'excluded', 'failed'),
                       'running': ('running', 'verified', 'failed', 'excluded'), 'failed': ('running',),
                       'verified': (), 'excluded': ()}
            if status not in allowed[prior[-1] if prior else None]:
                raise ValueError('Invalid status transition; successful runs are immutable')
            if status == 'verified' and validation is not True:
                raise ValueError('Verified status requires explicit passing validation')
            event = self._append('status', status=status, validation=validation, interpretation=interpretation,
                                 limitations=list(limitations), slurm_job_id=slurm_job_id)
            if status in ('verified', 'excluded'):
                _atomic_new(self.root/'seal.json', dict(events=event['sequence']+1, last_sha256=event['event_sha256'], run_identity=self.identity))
            return event

    def checkpoint(self, key, value):
        if not re.fullmatch('[A-Za-z0-9_.-]+', key):
            raise ValueError('Simple checkpoint key required')
        with self._lock():
            events = self._current_events()
            matches = [r for r in events if r['kind'] == 'checkpoint' and r['key'] == key]
            if matches:
                existing = json.loads((self.root/matches[0]['artifacts'][0]['path']).read_text())
                if existing != value:
                    raise ValueError('Checkpoint already exists with different values')
                return existing
            status = [r['status'] for r in events if r['kind'] == 'status']
            if not status or status[-1] != 'running':
                raise ValueError('Only running experiments can add checkpoints')
            path = self.root/'checkpoints'/f'{key}.json'
            if path.exists():
                raise ValueError('Unregistered checkpoint exists; inspect interrupted write before resuming')
            _atomic_new(path, value)
            self._append('checkpoint', key=key, artifacts=[dict(path=str(path.relative_to(self.root)), sha256=file_hash(path))])
            return value

    def load_checkpoint(self, key):
        matches = [r for r in self._current_events() if r['kind'] == 'checkpoint' and r['key'] == key]
        if not matches:
            return None
        artifact = matches[0]['artifacts'][0]
        target = self.root/artifact['path']
        if file_hash(target) != artifact['sha256']:
            raise ValueError('Checkpoint artifact hash changed')
        return json.loads(target.read_text())

    def report(self):
        events = self.events()
        states = [r for r in events if r['kind'] == 'status']
        return dict(schema_version=1, experiment_id=self.run.experiment_id, hypothesis=self.run.hypothesis,
            source_commit=self.run.source_commit, run_identity=self.identity,
            status=states[-1]['status'] if states else None, last_status=states[-1] if states else None,
            checkpoints=sum(r['kind'] == 'checkpoint' for r in events), events=len(events), hashes_verified=True,
            artifacts=[a for r in events for a in r.get('artifacts', [])])
