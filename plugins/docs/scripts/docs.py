#!/usr/bin/env python3
"""Docs helper for the documentation standard: mint ids, keep the decision index, check structure.

  docs.py adr "<title>"     new ADR in docs/decisions/, status Proposed; refreshes the index
  docs.py id REQ|NFR        print a fresh timestamp id for a requirement
  docs.py index             rewrite docs/decisions/README.md from the ADR headers
  docs.py check             structural health; exit 1 on any problem

`check` covers ADR headers and links, relative Markdown links and their anchors, and ids
(REQ, NFR, OBJ): each defined once with <a id="..."></a>, every mention resolving. Pages are
every Markdown file Git tracks outside dot-folders, plus README.md and docs/ on disk. It proves
structure only, never that a reader can use the docs. Run from the repo root or pass --root.
Standard library only.
"""
import argparse
import datetime
import re
import secrets
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote as url_unquote

STAMP = r"\d{8}-\d{6}-[0-9a-f]{4}"
ADR_ID = rf"ADR-{STAMP}"
ADR_ID_RE = re.compile(ADR_ID)
ADR_FILE_RE = re.compile(rf"^({ADR_ID})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
DOC_ID_RE = re.compile(rf"\b(?:(?:REQ|NFR)-{STAMP}|OBJ-\d+)\b")
CODE_ID_PATTERN = r"(REQ|NFR)-[0-9]{8}-[0-9]{6}-[0-9a-f]{4}"  # POSIX ERE for git grep: no \d
ANCHOR_RE = re.compile(r"""<a\s+(?:[^>]*\s)?(?:id|name)=["']([^"']+)["']""", re.I)
LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+[\"'][^\"']*[\"'])?\s*\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
STATUSES = ("Proposed", "Accepted", "Superseded", "Deprecated")
REQUIRED = ("adr", "title", "status", "date")
LIST_KEYS = ("supersedes", "amends", "amended_by", "refs")

ADR_TEMPLATE = """---
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

# {title}

## Context

## Decision

## Consequences

## Alternatives considered

## What would prove this wrong
"""


def stamp():
    return f"{datetime.datetime.now(datetime.timezone.utc):%Y%m%d-%H%M%S}-{secrets.token_hex(2)}"


# ---- ADR headers -------------------------------------------------------------------------

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


def parse_header(path):
    """Return (header dict, body, error). The header is flat `key: value` lines between ---."""
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


def load_adrs(adr_dir):
    adrs, errors = {}, []
    for path in sorted(adr_dir.glob("ADR-*.md")):
        match = ADR_FILE_RE.match(path.name)
        if not match:
            errors.append(f"{path}: name is not <id>-<kebab-slug>.md with id {ADR_ID}")
            continue
        meta, body, error = parse_header(path)
        if error:
            errors.append(f"{path}: {error}")
            continue
        adrs[match.group(1)] = {"path": path, "meta": meta, "body": body}
    return adrs, errors


def links(record, key):
    return as_list(record["meta"].get(key, ""))


def check_adrs(adrs):
    errors = []
    for aid, rec in adrs.items():
        meta = rec["meta"]
        err = lambda msg, p=rec["path"]: errors.append(f"{p}: {msg}")
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
        rows.append(f"| [{title}]({rec['path'].name}) | {status} | {unquote(meta.get('date', ''))} | {aid} |")
    return "\n".join([
        "# Decisions",
        "",
        "<!-- Generated by docs.py index from each ADR's header. Do not edit by hand. -->",
        "",
        "| Decision | Status | Date | Id |",
        "|---|---|---|---|",
        *rows,
        "",
    ])


def write_index(adr_dir, adrs):
    adr_dir.mkdir(parents=True, exist_ok=True)
    (adr_dir / "README.md").write_text(render_index(adrs), encoding="utf-8")


def new_adr(adr_dir, title):
    aid = f"ADR-{stamp()}"
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60].strip("-") or "decision"
    adr_dir.mkdir(parents=True, exist_ok=True)
    path = adr_dir / f"{aid}-{slug}.md"
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    path.write_text(ADR_TEMPLATE.format(id=aid, title=title.replace('"', "'"), date=today), encoding="utf-8")
    adrs, _ = load_adrs(adr_dir)
    write_index(adr_dir, adrs)
    return path


# ---- Markdown pages ----------------------------------------------------------------------

def prose_lines(text):
    """Yield (line number, line) outside fenced code, with inline code blanked out."""
    fence = None
    for number, line in enumerate(text.splitlines(), 1):
        match = FENCE_RE.match(line)
        if match:
            fence = None if fence == match.group(1) else (fence or match.group(1))
            continue
        if fence is None:
            yield number, re.sub(r"`[^`]*`", "", line)


def slug(heading):
    """GitHub's heading anchor: lower case, punctuation dropped, spaces to hyphens."""
    text = re.sub(r"<[^>]+>", "", heading)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return re.sub(r"[^\w\- ]", "", text.strip().lower()).replace(" ", "-")


def anchors(text):
    found, seen = set(), {}
    for _, line in prose_lines(text):
        found.update(ANCHOR_RE.findall(line))
        match = HEADING_RE.match(line)
        if match:
            base = slug(match.group(2))
            count = seen.get(base, 0)
            seen[base] = count + 1
            found.add(base if count == 0 else f"{base}-{count}")
    return found


def pages(root):
    """Every Markdown file Git tracks outside dot-folders, plus README.md and docs/ as they are on disk.

    Docs often live at the top level or in folder READMEs, so the check follows them there.
    Outside a Git repo, every Markdown file outside dot-folders counts.
    """
    try:
        listed = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--", "*.md"],
                                capture_output=True, text=True, check=False)
    except OSError:
        listed = None
    if listed and listed.returncode == 0:
        found = {root / name for name in listed.stdout.split("\0") if name}
    else:
        found = set(root.rglob("*.md"))
    found = {p for p in found if not any(part.startswith(".") for part in p.relative_to(root).parts)}
    found.add(root / "README.md")
    if (root / "docs").is_dir():
        found.update((root / "docs").rglob("*.md"))
    return sorted(p for p in found if p.is_file())


def check_pages(root, page_list, known_adrs):
    errors, defined, mentions = [], {}, []
    texts = {p: p.read_text(encoding="utf-8") for p in page_list}
    anchor_cache = {}

    def anchors_of(path):
        if path not in anchor_cache:
            anchor_cache[path] = anchors(texts.get(path) or path.read_text(encoding="utf-8"))
        return anchor_cache[path]

    for page, text in texts.items():
        rel = page.relative_to(root)
        for number, line in prose_lines(text):
            for target in LINK_RE.findall(line):
                if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I):
                    continue  # http:, mailto: and the like
                path_part, _, fragment = target.partition("#")
                dest = (page.parent / url_unquote(path_part)).resolve() if path_part else page
                if not dest.exists():
                    errors.append(f"{rel}:{number}: link to {target}, which does not exist")
                    continue
                if fragment and dest.suffix == ".md" and url_unquote(fragment) not in anchors_of(dest):
                    errors.append(f"{rel}:{number}: link to {target}, but that anchor does not exist")
            for ident in ANCHOR_RE.findall(line):
                if DOC_ID_RE.fullmatch(ident):
                    defined.setdefault(ident, []).append(f"{rel}:{number}")
            for ident in DOC_ID_RE.findall(line):
                mentions.append((ident, f"{rel}:{number}"))
            for ident in ADR_ID_RE.findall(line):
                if known_adrs is not None and ident not in known_adrs:
                    errors.append(f"{rel}:{number}: mentions {ident}, which does not exist")

    for ident, places in defined.items():
        if len(places) > 1:
            errors.append(f"{ident} is defined more than once: {', '.join(places)}")
    for ident, place in mentions:
        if ident not in defined:
            errors.append(f"{place}: mentions {ident}, which no page defines")
    return errors, set(defined)


def check_code_mentions(root, defined, page_list):
    """Requirement ids cited in tracked files that are not pages must exist too."""
    try:
        out = subprocess.run(["git", "-C", str(root), "grep", "-I", "-n", "-o", "-E", CODE_ID_PATTERN, "--", "."],
                             capture_output=True, text=True, check=False).stdout
    except OSError:
        return []
    errors, prose_cache = [], {}
    checked = {str(p.relative_to(root)) for p in page_list}
    for line in out.splitlines():
        place, _, ident = line.rpartition(":")
        name, _, number = place.rpartition(":")
        if name in checked:
            continue  # check_pages already read it
        if name.endswith(".md"):
            # Markdown in dot-folders (.claude/) may show an id as an example in code.
            if name not in prose_cache:
                text = (root / name).read_text(encoding="utf-8")
                prose_cache[name] = {n for n, prose in prose_lines(text) if ident_in(prose)}
            if int(number) not in prose_cache[name]:
                continue
        if ident not in defined:
            errors.append(f"{place}: mentions {ident}, which no page defines")
    return errors


def ident_in(text):
    return re.search(CODE_ID_PATTERN.replace("[0-9]", r"\d"), text) is not None


# ---- commands ----------------------------------------------------------------------------

def main(argv=None):
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", type=Path, default=Path("."), help="repo root (default .)")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("adr", parents=[common], help="write a new ADR").add_argument("title")
    sub.add_parser("id", parents=[common], help="print a fresh requirement id").add_argument(
        "kind", choices=["REQ", "NFR"])
    sub.add_parser("index", parents=[common], help="rewrite docs/decisions/README.md")
    sub.add_parser("check", parents=[common], help="structural health")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    adr_dir = root / "docs" / "decisions"
    if args.cmd == "adr":
        print(new_adr(adr_dir, args.title).relative_to(root))
        return 0
    if args.cmd == "id":
        print(f"{args.kind}-{stamp()}")
        return 0

    adrs, errors = load_adrs(adr_dir)
    if args.cmd == "index":
        write_index(adr_dir, adrs)
        print(f"docs: wrote {(adr_dir / 'README.md').relative_to(root)} ({len(adrs)} ADRs)")
        return 0

    errors += check_adrs(adrs)
    index = adr_dir / "README.md"
    if adrs and (not index.exists() or index.read_text(encoding="utf-8") != render_index(adrs)):
        errors.append(f"{index.relative_to(root)}: out of date, run `docs.py index`")
    page_list = pages(root)
    page_errors, defined = check_pages(root, page_list, set(adrs) if adr_dir.is_dir() else None)
    errors += page_errors + check_code_mentions(root, defined, page_list)
    for error in errors:
        print(error, file=sys.stderr)
    verdict = "FAILED" if errors else "passed"
    print(f"docs: structural check {verdict}: {len(page_list)} pages, {len(adrs)} ADRs, "
          f"{len(defined)} ids, {len(errors)} problems. Structure only; reader value is not checked.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
