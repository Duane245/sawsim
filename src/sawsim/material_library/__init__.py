"""Versioned local material registry; builtins are immutable through this API."""
import hashlib
import json
import os
import tempfile
from pathlib import Path
import re
from threading import RLock
from .schema import MaterialRecord

ROOT = Path(__file__).resolve().parent
BUILTIN_DIR = ROOT / 'builtin'
CUSTOM_DIR = Path(os.environ.get('SAWSIM_MATERIALS_DIR', str(Path.home() / '.sawsim' / 'materials'))) if not os.environ.get('SAWSIM_MATERIALS_INPLACE') else ROOT / 'custom'
_LOCK = RLock()


def _validated(record):
    return MaterialRecord.model_validate(record).model_dump()


def record_hash(record):
    """SHA-256 of canonical validated record JSON (all provenance included)."""
    raw = json.dumps(_validated(record), ensure_ascii=False, sort_keys=True,
                     separators=(',', ':'), allow_nan=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def _safe_identifier(value, version=False):
    pattern = r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}' if version else r'[a-z][a-z0-9_]{0,63}'
    if not isinstance(value, str) or re.fullmatch(pattern, value) is None:
        raise ValueError('Invalid material '+('version' if version else 'id'))


def _version_key(version):
    return tuple((1, int(part)) if part.isdigit() else (0, part)
                 for part in re.split(r'(\d+)', version))


def list_records():
    """Discover every version on each call. Return independent validated dicts."""
    result = []
    seen = set()
    with _LOCK:
        for directory in (BUILTIN_DIR, CUSTOM_DIR):
            if directory.is_symlink():
                raise ValueError('Material registry directories cannot be symlinks')
            for path in sorted(directory.glob('*.json')):
                if path.is_symlink():
                    raise ValueError('Material files cannot be symlinks')
                try:
                    record = _validated(json.loads(path.read_text(encoding='utf-8')))
                except (ValueError, OSError) as error:
                    raise ValueError('Invalid material record '+path.name+': '+str(error)) from error
                key = record['id'], record['version']
                if path.name != '%s__%s.json' % key:
                    raise ValueError('Material filename does not match id/version: '+path.name)
                if directory == CUSTOM_DIR and (not record['id'].startswith('user_') or record['status'] != 'user'):
                    raise ValueError('Custom materials require user_ id and user status')
                if key in seen:
                    raise ValueError('Duplicate material id/version: '+str(key))
                seen.add(key)
                result.append(record)
    return sorted(result, key=lambda r: (r['id'], _version_key(r['version'])))


def get_record(id, version=None):
    """Resolve explicit version, or latest using numeric-aware version sorting."""
    _safe_identifier(id)
    if version is not None:
        _safe_identifier(version, version=True)
    matches = [r for r in list_records() if r['id'] == id and (version is None or r['version'] == version)]
    if not matches:
        raise KeyError('Unknown material id/version: '+id+('/'+version if version else ''))
    return max(matches, key=lambda r: _version_key(r['version']))


def import_record(record):
    """Create a user record exactly once. Never replace any existing version."""
    validated = _validated(record)
    if not validated['id'].startswith('user_'):
        raise ValueError('Imported material id must start with user_')
    if validated['status'] != 'user':
        raise ValueError('Imported material status must be user')
    key = validated['id'], validated['version']
    payload = json.dumps(validated, ensure_ascii=False, indent=2, allow_nan=False)+'\n'
    with _LOCK:
        if any((r['id'], r['version']) == key for r in list_records()):
            raise FileExistsError('Material id/version already exists')
        CUSTOM_DIR.mkdir(parents=True, exist_ok=True)
        path = CUSTOM_DIR / ('%s__%s.json' % key)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                             prefix='.material_', suffix='.tmp',
                                             dir=str(CUSTOM_DIR), delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            # Publish a complete file atomically; link never replaces an existing
            # destination, including imports racing in separate service processes.
            os.link(str(temporary), str(path))
        except FileExistsError as error:
            raise FileExistsError('Material id/version already exists') from error
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    return validated


__all__ = ['MaterialRecord', 'list_records', 'get_record', 'record_hash', 'import_record']
