import re

from photofinder import i18n
from photofinder.i18n_zh import ZH

PLACEHOLDER = re.compile(r"\{\w+\}")
CANTONESE = re.compile("[嘅咗唔喺嘢冇睇啲嚟俾揾搵嗰佢呢㩒]")


def test_every_key_has_written_chinese():
    assert set(i18n.EN) == set(ZH)


def test_placeholders_match():
    for key, zh in ZH.items():
        assert sorted(PLACEHOLDER.findall(key)) == sorted(PLACEHOLDER.findall(zh)), key
        assert sorted(PLACEHOLDER.findall(key)) == sorted(PLACEHOLDER.findall(i18n.EN[key])), key


def test_no_cantonese_left_in_zh_text():
    bad = [v for v in ZH.values() if CANTONESE.search(v)]
    assert not bad, bad


def test_tr_uses_written_chinese():
    i18n.set_lang("zh")
    assert i18n.tr("共 {n} 張", n=3) == "共 3 张"
    i18n.set_lang("en")
    assert i18n.tr("共 {n} 張", n=3) == "3 photos"
    i18n.set_lang("zh")
