"""Notebook (nbformat 4 JSON) cleaning operations."""
import copy
import re

KEEP_NOTEBOOK_META = ("kernelspec", "language_info")
NOISY_CELL_META = ("execution", "collapsed", "scrolled", "ExecuteTime", "heading_collapsed", "hidden", "jupyter")
SECRET_PATTERNS = [
    ("aws-access-key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("github-token", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}")),
    ("api-key-assignment", re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[=:]\s*['\"][^'\"]{8,}['\"]")),
    ("slack-token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
]


def clean_notebook(nb, keep_outputs=False, keep_counts=False, keep_tags=True, strip_widgets=True, max_output_kb=None):
    """Return a cleaned copy of a notebook dict.

    - outputs removed (or, with keep_outputs, only those larger than max_output_kb)
    - execution counts reset, noisy cell metadata removed (tags kept by default)
    - notebook metadata reduced to kernelspec and language_info (drops widget state, signatures)
    """
    nb = copy.deepcopy(nb)
    meta = nb.get("metadata", {})
    nb["metadata"] = {k: meta[k] for k in KEEP_NOTEBOOK_META if k in meta}
    if not strip_widgets and "widgets" in meta:
        nb["metadata"]["widgets"] = meta["widgets"]
    for cell in nb.get("cells", []):
        cm = cell.get("metadata", {})
        cell["metadata"] = {k: v for k, v in cm.items() if k not in NOISY_CELL_META and (keep_tags or k != "tags")}
        if cell.get("cell_type") == "code":
            if not keep_outputs:
                cell["outputs"] = []
            elif max_output_kb is not None:
                cell["outputs"] = [o for o in cell.get("outputs", []) if len(str(o)) <= max_output_kb * 1024]
            if not keep_counts:
                cell["execution_count"] = None
                for o in cell.get("outputs", []):
                    if "execution_count" in o:
                        o["execution_count"] = None
        if cell.get("cell_type") == "markdown" and "attachments" in cell and not cell["attachments"]:
            del cell["attachments"]
    return nb


def is_clean(nb, **kw):
    return clean_notebook(nb, **kw) == nb


def _source(cell):
    s = cell.get("source", "")
    return "".join(s) if isinstance(s, list) else s


def scan_secrets(nb):
    """Find likely credentials in cell sources and outputs. Returns [(cell_index, kind, snippet)]."""
    hits = []
    for i, cell in enumerate(nb.get("cells", [])):
        texts = [_source(cell)]
        for o in cell.get("outputs", []):
            t = o.get("text") or o.get("data", {}).get("text/plain", "")
            texts.append("".join(t) if isinstance(t, list) else str(t))
        for t in texts:
            for kind, rx in SECRET_PATTERNS:
                for m in rx.finditer(t):
                    s = m.group(0)
                    hits.append((i, kind, s[:6] + "..." + s[-2:] if len(s) > 10 else s))
    return hits


def stats(nb):
    cells = nb.get("cells", [])
    code = [c for c in cells if c.get("cell_type") == "code"]
    out_bytes = sum(len(str(o)) for c in code for o in c.get("outputs", []))
    counts = [c.get("execution_count") for c in code if c.get("execution_count") is not None]
    return {"cells": len(cells), "code_cells": len(code), "output_kb": round(out_bytes / 1024, 1),
            "out_of_order": counts != sorted(counts), "empty_code_cells": sum(1 for c in code if not _source(c).strip())}
