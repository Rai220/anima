#!/usr/bin/env python3
"""
self_test.py — Validates all micro-tools in the toolkit.

Checks:
  - HTML files parse without errors
  - Python scripts import and run --help without errors
  - index.html links match actual files
  - No broken internal references

Usage:
  python3 self_test.py          # Run all checks
  python3 self_test.py -v       # Verbose output
"""

import os
import sys
import subprocess
import re
from html.parser import HTMLParser
from pathlib import Path

TOOLS_DIR = Path(__file__).parent
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
CHECK = '✓'
CROSS = '✗'
WARN = '!'

verbose = '-v' in sys.argv or '--verbose' in sys.argv
passed = 0
failed = 0
warnings = 0


def log_pass(msg):
    global passed
    passed += 1
    print(f'  {GREEN}{CHECK}{RESET} {msg}')


def log_fail(msg):
    global failed
    failed += 1
    print(f'  {RED}{CROSS}{RESET} {msg}')


def log_warn(msg):
    global warnings
    warnings += 1
    print(f'  {YELLOW}{WARN}{RESET} {msg}')


def log_info(msg):
    if verbose:
        print(f'    {msg}')


# --- Checks ---

class HTMLValidator(HTMLParser):
    VOID = {'br', 'hr', 'img', 'input', 'meta', 'link', 'area', 'base',
            'col', 'embed', 'source', 'track', 'wbr'}

    def __init__(self):
        super().__init__()
        self.errors = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            self.errors.append(f'Mismatched closing tag: </{tag}>')


def check_html_files():
    print('\n📄 HTML Files')
    html_files = sorted(TOOLS_DIR.glob('*.html'))

    if not html_files:
        log_fail('No HTML files found')
        return

    for f in html_files:
        content = f.read_text(encoding='utf-8')
        validator = HTMLValidator()
        try:
            validator.feed(content)
            if validator.errors:
                log_fail(f'{f.name}: {validator.errors[0]}')
            elif validator.stack:
                log_fail(f'{f.name}: Unclosed tags: {validator.stack}')
            else:
                size_kb = len(content) / 1024
                log_pass(f'{f.name} ({size_kb:.1f} KB)')
                log_info(f'Tags OK, no parsing errors')
        except Exception as e:
            log_fail(f'{f.name}: Parse error: {e}')

        # Check for basic structure
        if '<!DOCTYPE html>' not in content[:50]:
            log_warn(f'{f.name}: Missing DOCTYPE')
        if '<title>' not in content:
            log_warn(f'{f.name}: Missing <title>')


def check_python_files():
    print('\n🐍 Python Files')
    py_files = sorted(TOOLS_DIR.glob('*.py'))
    py_files = [f for f in py_files if f.name != 'self_test.py']

    if not py_files:
        log_warn('No Python tool files found')
        return

    for f in py_files:
        # Syntax check
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', str(f)],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                log_pass(f'{f.name}: Syntax OK')
            else:
                log_fail(f'{f.name}: Syntax error: {result.stderr.strip()}')
                continue
        except subprocess.TimeoutExpired:
            log_fail(f'{f.name}: Compilation timeout')
            continue

        # Help check (should not crash)
        try:
            result = subprocess.run(
                [sys.executable, str(f), '--help'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                log_pass(f'{f.name}: --help OK')
                log_info(result.stdout.split('\n')[0] if result.stdout else '(no output)')
            else:
                log_warn(f'{f.name}: --help returned code {result.returncode}')
        except subprocess.TimeoutExpired:
            log_fail(f'{f.name}: --help timeout')


def check_index_links():
    print('\n🔗 Index Links')
    index_path = TOOLS_DIR / 'index.html'

    if not index_path.exists():
        log_fail('index.html not found')
        return

    content = index_path.read_text(encoding='utf-8')
    hrefs = re.findall(r'href="([^"]+\.html)"', content)

    if not hrefs:
        log_fail('No tool links found in index.html')
        return

    actual_files = {f.name for f in TOOLS_DIR.glob('*.html') if f.name != 'index.html'}

    # Check all links resolve
    for href in hrefs:
        target = TOOLS_DIR / href
        if target.exists():
            log_pass(f'Link OK: {href}')
        else:
            log_fail(f'Broken link: {href}')

    # Check all tools are linked
    linked = set(hrefs)
    unlinked = actual_files - linked
    for f in sorted(unlinked):
        log_warn(f'Not in index: {f}')

    log_info(f'{len(hrefs)} links, {len(actual_files)} HTML tools')


def check_file_sizes():
    print('\n📊 File Sizes')
    all_files = sorted(TOOLS_DIR.glob('*'))
    all_files = [f for f in all_files if f.is_file() and not f.name.startswith('.')]

    total = 0
    for f in all_files:
        size = f.stat().st_size
        total += size
        if verbose:
            log_info(f'{f.name}: {size / 1024:.1f} KB')

    log_pass(f'Total: {total / 1024:.1f} KB across {len(all_files)} files')

    # Check for unreasonably large files
    for f in all_files:
        if f.stat().st_size > 100_000:
            log_warn(f'{f.name} is large ({f.stat().st_size / 1024:.0f} KB)')


def check_no_external_deps():
    print('\n📦 Dependencies')
    py_files = sorted(TOOLS_DIR.glob('*.py'))
    py_files = [f for f in py_files if f.name != 'self_test.py']

    stdlib = {
        'sys', 'os', 'math', 'string', 'argparse', 'secrets', 'json',
        'pathlib', 'subprocess', 're', 'html', 'html.parser',
        'collections', 'functools', 'itertools', 'hashlib', 'base64',
        'io', 'textwrap', 'datetime', 'time', 'struct', 'enum',
        'typing', 'dataclasses', 'abc', 'contextlib', 'unittest',
        'http', 'socketserver', 'webbrowser', 'urllib', 'shutil',
    }

    for f in py_files:
        content = f.read_text(encoding='utf-8')
        imports = re.findall(r'^(?:import|from)\s+(\w+)', content, re.MULTILINE)
        external = [i for i in imports if i not in stdlib and not i.startswith('_')]
        if external:
            log_warn(f'{f.name}: Possible external deps: {external}')
        else:
            log_pass(f'{f.name}: Zero external dependencies')


def check_functional():
    """Functional tests — verify tools produce correct output."""
    print('\n🧪 Functional Tests')

    # password.py: generate password of correct length
    try:
        result = subprocess.run(
            [sys.executable, str(TOOLS_DIR / 'password.py'), '-n', '20', '-q'],
            capture_output=True, text=True, timeout=10
        )
        pw = result.stdout.strip()
        if len(pw) == 20:
            log_pass(f'password.py: 20-char password generated ({len(pw)} chars)')
        else:
            log_fail(f'password.py: Expected 20 chars, got {len(pw)}: "{pw}"')
    except Exception as e:
        log_fail(f'password.py functional: {e}')

    # password.py: passphrase word count
    try:
        result = subprocess.run(
            [sys.executable, str(TOOLS_DIR / 'password.py'), '-w', '5', '-q'],
            capture_output=True, text=True, timeout=10
        )
        phrase = result.stdout.strip()
        word_count = len(phrase.split('-'))
        if word_count == 5:
            log_pass(f'password.py: 5-word passphrase OK')
        else:
            log_fail(f'password.py: Expected 5 words, got {word_count}: "{phrase}"')
    except Exception as e:
        log_fail(f'password.py passphrase: {e}')

    # password.py: PIN is digits only
    try:
        result = subprocess.run(
            [sys.executable, str(TOOLS_DIR / 'password.py'), '--pin', '6', '-q'],
            capture_output=True, text=True, timeout=10
        )
        pin = result.stdout.strip()
        if len(pin) == 6 and pin.isdigit():
            log_pass(f'password.py: 6-digit PIN OK')
        else:
            log_fail(f'password.py: Bad PIN: "{pin}"')
    except Exception as e:
        log_fail(f'password.py PIN: {e}')

    # password.py: batch mode
    try:
        result = subprocess.run(
            [sys.executable, str(TOOLS_DIR / 'password.py'), '-c', '3', '-q'],
            capture_output=True, text=True, timeout=10
        )
        lines = [l for l in result.stdout.strip().split('\n') if l.strip()]
        if len(lines) == 3:
            log_pass(f'password.py: Batch of 3 OK')
        else:
            log_fail(f'password.py: Batch expected 3 lines, got {len(lines)}')
    except Exception as e:
        log_fail(f'password.py batch: {e}')

    # qr.py: terminal output structure
    try:
        result = subprocess.run(
            [sys.executable, str(TOOLS_DIR / 'qr.py'), 'TEST'],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout
        if '█' in output and len(output) > 50:
            log_pass(f'qr.py: Terminal QR rendered ({len(output)} chars)')
        else:
            log_fail(f'qr.py: No QR blocks in output')
    except Exception as e:
        log_fail(f'qr.py terminal: {e}')

    # qr.py: SVG output
    try:
        svg_path = TOOLS_DIR / '_test_qr.svg'
        result = subprocess.run(
            [sys.executable, str(TOOLS_DIR / 'qr.py'), '-o', str(svg_path), 'HELLO'],
            capture_output=True, text=True, timeout=10
        )
        if svg_path.exists():
            content = svg_path.read_text()
            if '<svg' in content and 'viewBox' in content:
                log_pass(f'qr.py: SVG output valid')
            else:
                log_fail(f'qr.py: SVG missing required elements')
            svg_path.unlink()
        else:
            log_fail(f'qr.py: SVG file not created')
    except Exception as e:
        log_fail(f'qr.py SVG: {e}')

    # qr.py: stdin pipe
    try:
        result = subprocess.run(
            [sys.executable, str(TOOLS_DIR / 'qr.py')],
            input='PIPE_TEST', capture_output=True, text=True, timeout=10
        )
        if '█' in result.stdout:
            log_pass(f'qr.py: Stdin pipe OK')
        else:
            log_fail(f'qr.py: Stdin pipe failed')
    except Exception as e:
        log_fail(f'qr.py pipe: {e}')

    # password.py: wordlist integrity
    try:
        sys.path.insert(0, str(TOOLS_DIR))
        import importlib
        pw_mod = importlib.import_module('password')
        importlib.reload(pw_mod)
        wl = pw_mod.WORDLIST
        if len(wl) == 1024:
            log_pass(f'password.py: Wordlist is exactly 1024 words')
        else:
            log_fail(f'password.py: Wordlist has {len(wl)} words, expected 1024')
        if len(set(wl)) == len(wl):
            log_pass(f'password.py: No duplicate words')
        else:
            log_fail(f'password.py: Duplicate words found')
    except Exception as e:
        log_fail(f'password.py wordlist: {e}')

    # serve.py: starts and serves index.html
    try:
        import urllib.request
        import time
        import random
        port = 18700 + random.randint(50, 99)
        proc = subprocess.Popen(
            [sys.executable, str(TOOLS_DIR / 'serve.py'), '-p', str(port)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        connected = False
        for attempt in range(4):
            time.sleep(0.5 + attempt * 0.5)
            try:
                resp = urllib.request.urlopen(f'http://localhost:{port}/', timeout=3)
                if resp.status == 200 and b'Micro Tools' in resp.read():
                    log_pass('serve.py: Starts and serves index.html')
                    connected = True
                    break
            except Exception:
                continue
        if not connected:
            log_fail('serve.py: Cannot connect after retries')
        proc.terminate()
        proc.wait(timeout=5)
    except Exception as e:
        log_fail(f'serve.py functional: {e}')


# --- Main ---

def main():
    print('🔧 Micro-Tools Self-Test')
    print(f'   Directory: {TOOLS_DIR}')

    check_html_files()
    check_python_files()
    check_index_links()
    check_no_external_deps()
    check_functional()
    check_file_sizes()

    print(f'\n{"=" * 40}')
    print(f'  {GREEN}{passed} passed{RESET}', end='')
    if failed:
        print(f'  {RED}{failed} failed{RESET}', end='')
    if warnings:
        print(f'  {YELLOW}{warnings} warnings{RESET}', end='')
    print()

    if failed:
        print(f'\n  {RED}FAIL{RESET}')
        sys.exit(1)
    else:
        print(f'\n  {GREEN}ALL CHECKS PASSED{RESET}')


if __name__ == '__main__':
    main()
