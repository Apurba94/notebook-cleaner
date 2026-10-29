"""Command-line interface for notebook-cleaner."""
import argparse
import json
import sys

from .core import clean_notebook, is_clean, scan_secrets, stats


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _save(nb, path):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(nb, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="notebook-cleaner", description="Strip outputs and metadata from notebooks.")
    ap.add_argument("notebooks", nargs="+")
    ap.add_argument("--check", action="store_true", help="do not modify; exit 1 if any notebook is not clean (CI/pre-commit)")
    ap.add_argument("--keep-outputs", action="store_true")
    ap.add_argument("--max-output-kb", type=float, help="with --keep-outputs, drop outputs larger than this")
    ap.add_argument("--keep-counts", action="store_true")
    ap.add_argument("--drop-tags", action="store_true")
    ap.add_argument("--secrets", action="store_true", help="scan for credentials (exit 1 if found)")
    ap.add_argument("--stats", action="store_true")
    args = ap.parse_args(argv)
    opts = dict(keep_outputs=args.keep_outputs, keep_counts=args.keep_counts, keep_tags=not args.drop_tags,
                max_output_kb=args.max_output_kb)
    dirty, leaks = [], 0
    for p in args.notebooks:
        nb = _load(p)
        if args.stats:
            print("%s: %s" % (p, json.dumps(stats(nb))))
        if args.secrets:
            for i, kind, snip in scan_secrets(nb):
                print("%s: cell %d: possible %s (%s)" % (p, i, kind, snip))
                leaks += 1
        if args.check:
            if not is_clean(nb, **opts):
                dirty.append(p)
                print("NOT CLEAN: %s" % p)
        elif not args.stats and not args.secrets or not is_clean(nb, **opts) and not (args.stats or args.secrets):
            cleaned = clean_notebook(nb, **opts)
            if cleaned != nb:
                _save(cleaned, p)
                print("cleaned %s" % p)
    if dirty:
        print("%d notebook(s) need cleaning: run notebook-cleaner %s" % (len(dirty), " ".join(dirty)), file=sys.stderr)
    return 1 if dirty or leaks else 0
