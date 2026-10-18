"""Validate a local UI delivery manifest, not runtime behavior. No writes to project."""
import argparse
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

MAX_FILES = 256
MAX_TOTAL = 32 * 1024 * 1024


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_file(root, name):
    if not isinstance(name, str) or not name or '\\' in name:
        raise ValueError('File paths must be nonempty relative POSIX paths')
    rel = PurePosixPath(name)
    if rel.is_absolute() or any(p in ('.', '..') for p in name.split('/')):
        raise ValueError('Expected a project-relative file: ' + name)
    path = root.joinpath(*rel.parts)
    if any(p.is_symlink() for p in [path, *path.parents] if p != root.parent and p.is_relative_to(root)):
        raise ValueError('Project assets must be ordinary files: ' + name)
    if not path.is_file() or not path.resolve().is_relative_to(root):
        raise ValueError('Missing local file: ' + name)
    return path


class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.references = []
        self.lang = None
        self.viewport = False
        self.titles = 0
        self.h1 = 0
        self.inline_styles = []
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html':
            self.lang = a.get('lang')
        if tag == 'meta' and a.get('name') == 'viewport':
            self.viewport = bool(a.get('content'))
        self.titles += tag == 'title'
        self.h1 += tag == 'h1'
        if tag == 'base':
            raise ValueError('A local prototype must not redefine its URL base')
        if tag in ('iframe', 'object', 'embed'):
            raise ValueError('Embedded remote/document runtimes are outside this local prototype contract')
        if tag == 'style':
            self.in_style = True
        if 'style' in a:
            self.inline_styles.append(a['style'])
        for attr in ('src', 'href', 'poster'):
            if a.get(attr):
                self.references.append(a[attr])
        if a.get('srcset'):
            self.references.extend(item.strip().split()[0] for item in a['srcset'].split(','))

    def handle_endtag(self, tag):
        if tag == 'style':
            self.in_style = False

    def handle_data(self, data):
        if self.in_style:
            self.inline_styles.append(data)


def css_references(text):
    refs = re.findall(r'url\(\s*[\'"]?([^\s)\'"]+)', text, re.I)
    refs += re.findall(r'@import\s+[\'"]([^\'"]+)', text, re.I)
    return refs


def validate(project):
    root = project.resolve()
    manifest_path = local_file(root, 'project.json')
    if manifest_path.stat().st_size > 256 * 1024:
        raise ValueError('Project manifest exceeds 256 KiB')
    m = json.loads(manifest_path.read_text(encoding='utf-8'))
    if m.get('schema_version') != 1 or m.get('mode') != 'local-prototype':
        raise ValueError('Expected schema_version1 and mode local-prototype')
    for field in ('title', 'brief', 'entry', 'readme', 'tokens'):
        if not isinstance(m.get(field), str) or not m[field]:
            raise ValueError('Missing project field: ' + field)
    files = m.get('files')
    if not isinstance(files, list) or not 1 <= len(files) <= MAX_FILES or len(set(files)) != len(files):
        raise ValueError('files must contain 1..256 unique relative paths')
    paths = {name: local_file(root, name) for name in files}
    for field in ('brief', 'entry', 'readme', 'tokens'):
        if m[field] not in paths:
            raise ValueError(field + ' must be declared in files')
    if paths[m['entry']].suffix.lower() != '.html':
        raise ValueError('entry must be local HTML')
    if sum(p.stat().st_size for p in paths.values()) > MAX_TOTAL:
        raise ValueError('Project exceeds 32 MiB')
    for field in ('brief', 'tokens'):
        if m.get(field + '_sha256') != sha(paths[m[field]]):
            raise ValueError('Reviewed ' + field + ' hash mismatch')
    if not isinstance(m.get('asset_sources'), dict) or set(m['asset_sources']) != set(files):
        raise ValueError('asset_sources needs one honest provenance entry per file')
    if any(not isinstance(v, str) or not v.strip() for v in m['asset_sources'].values()):
        raise ValueError('Asset provenance entries must be nonempty strings')
    interactions = m.get('interactions')
    if not isinstance(interactions, list) or not interactions or any(not isinstance(i, str) or not i.strip() for i in interactions):
        raise ValueError('List concrete user interactions to validate in a browser')
    states = m.get('states', [])
    if not {'loading', 'empty', 'error', 'permission-denied', 'ready'} <= set(states):
        raise ValueError('Declare all required UI states and how to reach them in README')
    references = []
    for name, path in paths.items():
        if path.suffix.lower() == '.html':
            doc = Document()
            doc.feed(path.read_text(encoding='utf-8'))
            if not doc.lang or not doc.viewport or doc.titles != 1 or doc.h1 != 1:
                raise ValueError('Each HTML needs lang, viewport, one title and one h1: ' + name)
            references.extend((name, url) for url in doc.references)
            references.extend((name, url) for css in doc.inline_styles for url in css_references(css))
        elif path.suffix.lower() == '.css':
            references.extend((name, url) for url in css_references(path.read_text(encoding='utf-8')))
    for base, url in references:
        split = urlsplit(url)
        if split.scheme or split.netloc or split.path.startswith('/'):
            raise ValueError('Prototype resource/link must be local and relative: ' + url)
        if not split.path:
            continue
        rel = (PurePosixPath(base).parent / unquote(split.path)).as_posix()
        local_file(root, rel)
        if rel not in files:
            raise ValueError('Referenced asset missing from manifest: ' + rel)
    # This is an evidence manifest, not an execution sandbox or JS correctness proof.
    return {'schema_version': 1, 'expert_version': '0.1.0', 'title': m['title'],
            'mode': m['mode'], 'entry': m['entry'], 'source_manifest_sha256': sha(manifest_path),
            'files': {n: sha(p) for n, p in paths.items()}, 'static_validation': 'PASS',
            'runtime_validation': 'NOT RUN', 'responsive_validation': 'NOT RUN',
            'keyboard_validation': 'NOT RUN', 'console_validation': 'NOT RUN',
            'required_interactions': interactions,
            'limitations': ['Static reference checks do not validate JavaScript network requests, visual quality, or runtime behavior.',
                            'Browser evidence must be recorded separately; this is not Native Artifact registration.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path, help='New directory outside the project')
    args = parser.parse_args()
    try:
        if args.output.resolve().is_relative_to(args.project.resolve()):
            raise ValueError('Validation receipt must be outside the served project')
        result = validate(args.project)
        args.output.mkdir(parents=True, exist_ok=False)
        (args.output / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'static_validation': 'PASS', 'runtime_validation': 'NOT RUN', 'output': str(args.output.resolve())}, ensure_ascii=False))
    except (ValueError, OSError, KeyError, TypeError) as e:
        parser.exit(2, 'UI delivery incomplete: ' + str(e) + '\n')
