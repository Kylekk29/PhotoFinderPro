"""Safety: originals are never changed; copies never overwrite; writes stay in allowed folders."""
import hashlib
import os
import re
from pathlib import Path

import pytest

from photofinder import copier, lock

SRC_DIR = Path(__file__).resolve().parents[1] / "src" / "photofinder"
FORBIDDEN = re.compile(r"os\.remove|os\.unlink|os\.rmdir|os\.rename|os\.replace|shutil\.move|shutil\.rmtree"
                       r"|\.unlink\(|\.rmdir\(|\.rename\(|os\.utime|os\.chmod|os\.truncate")


def snap(p):
    st = os.stat(p)
    return hashlib.sha256(Path(p).read_bytes()).hexdigest(), st.st_mtime_ns, st.st_size


def test_source_code_has_no_delete_move_rename_calls():
    hits = []
    for f in SRC_DIR.glob("*.py"):
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if FORBIDDEN.search(line) and not line.lstrip().startswith(("#", '"')):
                hits.append(f"{f.name}:{n}: {line.strip()}")
    assert hits == []


def test_copy_keeps_source_unchanged_and_verifies(tmp_path, make_photo, home):
    src = make_photo("album", "a.png", 5)
    before = snap(src)
    out = tmp_path / "out"
    status, dest = copier.safe_copy(str(src), "confirmed", out)
    assert status == "copied"
    assert snap(dest)[0] == before[0]
    assert snap(src) == before
    assert out in dest.parents


def test_second_copy_is_already_there(tmp_path, make_photo, home):
    src = make_photo("album", "a.png", 5)
    out = tmp_path / "out"
    copier.safe_copy(str(src), "confirmed", out)
    status, _ = copier.safe_copy(str(src), "confirmed", out)
    assert status == "already_there"
    assert len(list((out / "confirmed" / "album").iterdir())) == 1


def test_same_name_different_content_gets_new_name_and_no_duplicates(tmp_path, make_photo, home):
    a = make_photo("album", "x.png", 5)
    out = tmp_path / "out"
    copier.safe_copy(str(a), "maybe", out)
    # same parent-folder name from another place, same file name, different content
    other = tmp_path / "elsewhere" / "album"
    other.mkdir(parents=True)
    b = other / "x.png"
    b.write_bytes(a.read_bytes() + b"1")
    s1, d1 = copier.safe_copy(str(b), "maybe", out)
    assert s1 == "copied" and d1.name == "x__2.png"
    # copying b again must NOT create x__3 (identical copy already exists under a numbered name)
    s2, d2 = copier.safe_copy(str(b), "maybe", out)
    assert s2 == "already_there" and d2 == d1
    assert sorted(p.name for p in (out / "maybe" / "album").iterdir()) == ["x.png", "x__2.png"]


def test_refuses_write_outside_allowed_roots(tmp_path):
    with pytest.raises(PermissionError):
        copier.inside_roots(tmp_path / "other" / "file.png", [tmp_path / "out"])


def test_output_folder_must_not_be_inside_or_contain_a_scanned_folder(tmp_path):
    photos = tmp_path / "photos"
    photos.mkdir()
    with pytest.raises(PermissionError):
        copier.validate_output_root(photos / "found", [photos])
    with pytest.raises(PermissionError):
        copier.validate_output_root(tmp_path, [photos])
    copier.validate_output_root(tmp_path / "found", [photos])  # sibling is fine


def test_single_instance_lock(tmp_path):
    a, b = lock.SingleInstance(tmp_path / "x.lock"), lock.SingleInstance(tmp_path / "x.lock")
    assert a.acquire() is True
    assert b.acquire() is False
    a.release()
    assert b.acquire() is True
    b.release()
