"""Every tr("...") literal in the app must have an English text with the same {placeholders}."""
import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

SRC = Path(__file__).resolve().parents[1] / "src" / "photofinder"
HOLES = re.compile(r"\{(\w+)\}")


def _literals():
    """All first arguments of tr(...) calls. AST (not a regex) so adjacent literals and quote styles just work."""
    found = {}
    for p in SRC.rglob("*.py"):
        for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "tr" and node.args:
                a = node.args[0]
                assert isinstance(a, ast.Constant) and isinstance(a.value, str), f"{p.name}:{node.lineno} tr() needs a literal"
                found.setdefault(a.value, f"{p.name}:{node.lineno}")
    return found


def test_every_tr_literal_has_english_with_same_placeholders():
    from photofinder import i18n
    lits = _literals()
    assert len(lits) > 100
    missing = [f"{where} {k!r}" for k, where in lits.items() if k not in i18n.EN]
    assert not missing, "no English for:\n" + "\n".join(missing)
    bad = [k for k in lits if set(HOLES.findall(k)) != set(HOLES.findall(i18n.EN[k]))]
    assert not bad, f"placeholders differ: {bad}"


def test_no_stale_english_entries():
    from photofinder import i18n
    lits = set(_literals())
    stale = [k for k in i18n.EN if k not in lits and k != "重新開啟程式後生效"]
    assert not stale, f"unused EN keys: {stale}"


def test_set_lang_switches_tr():
    from photofinder import i18n
    try:
        i18n.set_lang("en")
        assert i18n.tr("共 {n} 張", n=3) == "3 photos"
        i18n.set_lang("zh")
        assert i18n.tr("共 {n} 張", n=3) == "共 3 張"
        i18n.set_lang("xx")   # unknown -> zh
        assert i18n.lang() == "zh"
        assert i18n.tr("未知文字") == "未知文字"
    finally:
        i18n.set_lang("zh")
