from types import SimpleNamespace

from app.services.nexus_ai.simple_extractor import extract_text_from_file


def test_legacy_doc_uses_bounded_antiword_extraction(monkeypatch, tmp_path) -> None:
    path = tmp_path / "resume.doc"
    path.write_bytes(b"legacy-doc")
    monkeypatch.setattr("app.services.nexus_ai.simple_extractor.shutil.which", lambda _name: "/usr/bin/antiword")
    monkeypatch.setattr(
        "app.services.nexus_ai.simple_extractor.subprocess.run",
        lambda command, **kwargs: SimpleNamespace(returncode=0, stdout=b"Jane Doe\nData Engineer"),
    )

    assert "Data Engineer" in extract_text_from_file(str(path))
