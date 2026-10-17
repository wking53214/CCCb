"""CCCb is independent of CNS, and these tests hold whether or not CNS is installed.

Each runs in a fresh interpreter in which ``cns`` is blocked outright
(``sys.modules['cns'] = None`` makes any import of it fail), so the result does not
depend on what the test environment happens to contain. They never skip.

The package is found where it is imported from (a checkout or, in CI, the installed
copy); ``pyproject.toml`` is read from the directory above ``tests``.
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
import textwrap
import tomllib
from pathlib import Path

import cccb

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = Path(cccb.__file__).resolve().parent
BLOCK = "import sys; sys.modules['cns'] = None; sys.modules['cns.gate'] = None\n"
ENV = {"PYTHONPATH": str(PACKAGE.parent), "PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONDONTWRITEBYTECODE": "1"}
HINT = "pip install 'cccb[cns]'"
LONG = ("This exact sentence about the retry path never re-reading the lease "
        "was resubmitted word for word to inflate the anomaly count.")


def run(code: str, *, block: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-c", (BLOCK if block else "") + textwrap.dedent(code)],
                          capture_output=True, text=True, env=ENV, timeout=120, check=False)


def ok(done: subprocess.CompletedProcess) -> None:
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip().endswith("ok"), done.stdout


def test_the_package_and_its_connector_import_with_cns_blocked():
    ok(run("import cccb, cccb.cns_connector; print('ok')"))


def test_the_matcher_still_does_its_job_with_cns_blocked():
    ok(run(f"""
        from cccb import TextMatcher
        m = TextMatcher()
        m.add("d1", {LONG!r})
        item_id, anti_probability, match_length = m.duplicate_of("prefix " + {LONG!r})
        assert item_id == "d1" and anti_probability < 1e-9 and match_length >= 40
        m.add("p1", "the governance terminology inflated again into grandiose pseudo-technical jargon")
        best_id, score, matches = m.recurrence_of("governance terminology inflated once more, grandiose jargon returning")
        assert best_id == "p1" and matches[0] == (best_id, score)
        print('ok')
    """))


def test_the_connector_says_what_is_missing_when_cns_is_blocked():
    ok(run(f"""
        from cccb.cns_connector import (CnsNotInstalled, binds, cns_available, duplicate_content, duplicate_digest,
                                        duplicate_finding, recurrence_digest, recurrence_finding)
        assert cns_available() is False
        dup = duplicate_finding("prefix " + {LONG!r}, {LONG!r})
        rec = recurrence_finding("governance terminology inflated again", "governance terminology inflated once")
        assert duplicate_content(dup)["kind"] == "duplicate"   # plain data, no cns needed
        for call in (lambda: duplicate_digest(dup), lambda: recurrence_digest(rec), lambda: binds(object(), dup)):
            try:
                call()
            except CnsNotInstalled as e:
                assert {HINT!r} in str(e)
                assert isinstance(e, ImportError)
            else:
                raise SystemExit("ran without cns")
        print('ok')
    """))


def test_importing_the_package_does_not_load_cns_even_when_it_is_installed():
    ok(run("""
        import sys
        import cccb, cccb.cns_connector
        assert not [m for m in sys.modules if m == "cns" or m.startswith("cns.")], "cns was loaded"
        print('ok')
    """, block=False))


def test_no_module_of_the_package_imports_cns_by_statement():
    offenders = {}
    for path in PACKAGE.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else \
                [node.module] if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module else []
            bad = [n for n in names if n == "cns" or n.startswith("cns.")]
            if bad:
                offenders.setdefault(str(path.relative_to(PACKAGE)), []).extend(bad)
    assert offenders == {}


def test_the_package_declares_no_runtime_dependency_and_pins_the_cns_extra():
    meta = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert meta["dependencies"] == []
    assert meta["optional-dependencies"]["cns"] == ["cns @ git+https://github.com/wking53214/CNS.git@v1.8.0"]
