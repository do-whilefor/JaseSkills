from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.scope_guard import redact_text, contains_unredacted_secret

def redact_file(src, dst):
    text=Path(src).read_text(encoding='utf-8', errors='ignore')
    redacted,status=redact_text(text)
    Path(dst).parent.mkdir(parents=True,exist_ok=True); Path(dst).write_text(redacted,encoding='utf-8')
    return {'redaction_status':status,'unredacted_secret_remaining':contains_unredacted_secret(redacted)}
