#!/usr/bin/env python3
"""ADR helper: mint a new ADR, rebuild INDEX.md, check the corpus. Standard library only.

  adr.py new "<title>" [--dir docs/adr]   write <id>-<slug>.md from the template, refresh the index
  adr.py index [--dir docs/adr]           rewrite INDEX.md from the ADR headers
  adr.py check [--dir docs/adr]           exit 1 on any inconsistency (pre-commit, CI)

Ids are ADR-YYYYMMDD-HHMMSS-xxxx: UTC time plus 4 random hex digits. Each ADR opens with a
header block between --- lines, one `key: value` per line; lists use flow style [a, b].
"""
import argparse
import datetime
import re
import secrets
import sys
from pathlib import Path

ID = r"ADR-\d{8}-\d{6}-[0-9a-f]{4}"
ID_RE = re.compile(ID)
FILE_RE = re.compile(rf"^({ID})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
STATUSES = ("Proposed", "Accepted", "Superseded", "Deprecated")
REQUIRED = ("adr", "title", "status", "date")
LIST_KEYS = ("supersedes", "amends", "amended_by", "refs")

TEMPLATE = """---
adr: {id}
title: "{title}"
status: Proposed
date: {date}
supersedes: []
superseded_by:
amends: []
amended_by: []
refs: []
---

# {id}: {title}

## Context

## Decision

## Consequences

## Alternatives considered

## What would prove this wrong
"""


def unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def as_list(value):
    value = value.strip()
    if value in ("", "[]", "null", "~"):
        return []
    if value.startswith("[") and value.endswith("]"):
        return [unquote(item) for item in value[1:-1].split(",") if item.strip()]
    return [unquote(value)]


def parse(path):
    """Return (header dict, body, error). The header is flat `key: value` lines."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None, text, "no header block (the file must start with ---)"
    end = text.find("\n---", 3)
    if end < 0:
        return None, text, "header block is not closed with ---"
    meta = {}
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep or line[0].isspace():
            return None, text, f"header line is not flat `key: value`: {line!r}"
        meta[key.strip()] = value.strip()
    return meta, text[end + 4:], None


def load(adr_dir):
    adrs, errors = {}, []
    for path in sorted(adr_dir.glob("ADR-*.md")):
        match = FILE_RE.match(path.name)
        if not match:
            errors.append(f"{path.name}: name is not <id>-<kebab-slug>.md with id {ID}")
            continue
        meta, body, error = parse(path)
        if error:
            errors.append(f"{path.name}: {error}")
            continue
        adrs[match.group(1)] = {"path": path, "meta": meta, "body": body}
    return adrs, errors


def links(record, key):
    return as_list(record["meta"].get(key, ""))


def check(adrs):
    errors = []
    for aid, rec in adrs.items():
        meta, name = rec["meta"], rec["path"].name
        err = lambda msg: errors.append(f"{name}: {msg}")
        for key in REQUIRED:
            if not unquote(meta.get(key, "")):
                err(f"missing `{key}`")
        if meta.get("adr") and meta["adr"] != aid:
            err(f"header says {meta['adr']}, file name says {aid}")
        status = meta.get("status", "")
        if status and status not in STATUSES:
            err(f"status `{status}` is not one of {', '.join(STATUSES)}")
        if meta.get("date") and not DATE_RE.match(unquote(meta["date"])):
            err(f"date `{meta['date']}` is not YYYY-MM-DD")

        superseded_by = as_list(meta.get("superseded_by", ""))
        if len(superseded_by) > 1:
            err("`superseded_by` names more than one ADR")
        if (status == "Superseded") != bool(superseded_by):
            err("status Superseded and `superseded_by` must go together")

        for key in LIST_KEYS + ("superseded_by",):
            for target in as_list(meta.get(key, "")):
                if target not in adrs:
                    err(f"`{key}` points at {target}, which does not exist")
        for target in sorted(set(ID_RE.findall(rec["body"])) - {aid}):
            if target not in adrs:
                err(f"text refers to {target}, which does not exist")

        # Links are recorded on both ends, so either ADR read alone tells the truth.
        for target in links(rec, "supersedes"):
            if target in adrs and as_list(adrs[target]["meta"].get("superseded_by", "")) != [aid]:
                err(f"supersedes {target}, but {target} is not `superseded_by: {aid}`")
        for target in superseded_by:
            if target in adrs and aid not in links(adrs[target], "supersedes"):
                err(f"superseded by {target}, but {target} does not list it in `supersedes`")
        for key, back in (("amends", "amended_by"), ("amended_by", "amends")):
            for target in links(rec, key):
                if target in adrs and aid not in links(adrs[target], back):
                    err(f"`{key}` has {target}, but {target} does not list it in `{back}`")
    return errors


def render_index(adrs):
    rows = []
    for aid, rec in adrs.items():
        meta = rec["meta"]
        status = meta.get("status", "")
        for target in as_list(meta.get("superseded_by", "")):
            if target in adrs:
                status += f" by [{target}]({adrs[target]['path'].name})"
        title = unquote(meta.get("title", "")).replace("|", "\\|")
        rows.append(f"| [{aid}]({rec['path'].name}) | {title} | {status} | {unquote(meta.get('date', ''))} |")
    return "\n".join([
        "# Architecture decisions",
        "",
        "<!-- Generated by adr.py index from each ADR's header. Do not edit by hand. -->",
        "",
        "| ADR | Title | Status | Date |",
        "|---|---|---|---|",
        *rows,
        "",
    ])


def write_index(adr_dir, adrs):
    (adr_dir / "INDEX.md").write_text(render_index(adrs), encoding="utf-8")


def new(adr_dir, title):
    now = datetime.datetime.now(datetime.timezone.utc)
    aid = f"ADR-{now:%Y%m%d-%H%M%S}-{secrets.token_hex(2)}"
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60].strip("-") or "decision"
    adr_dir.mkdir(parents=True, exist_ok=True)
    path = adr_dir / f"{aid}-{slug}.md"
    path.write_text(TEMPLATE.format(id=aid, title=title.replace('"', "'"), date=f"{now:%Y-%m-%d}"),
                    encoding="utf-8")
    adrs, _ = load(adr_dir)
    write_index(adr_dir, adrs)
    return path


def main(argv=None):
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--dir", type=Path, default=Path("docs/adr"), help="ADR folder (default docs/adr)")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("new", parents=[common], help="write a new ADR").add_argument("title")
    sub.add_parser("index", parents=[common], help="rewrite INDEX.md")
    sub.add_parser("check", parents=[common], help="fail on inconsistencies")
    args = parser.parse_args(argv)

    if args.cmd == "new":
        print(new(args.dir, args.title))
        return 0
    adrs, errors = load(args.dir)
    if args.cmd == "index":
        write_index(args.dir, adrs)
        print(f"adr: wrote {args.dir / 'INDEX.md'} ({len(adrs)} ADRs)")
        return 0
    errors += check(adrs)
    index = args.dir / "INDEX.md"
    if adrs and (not index.exists() or index.read_text(encoding="utf-8") != render_index(adrs)):
        errors.append("INDEX.md: out of date, run `adr.py index`")
    for error in errors:
        print(error, file=sys.stderr)
    if not errors:
        print(f"adr: {len(adrs)} ADRs consistent")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
