"""Testes de cli/plugadvpl/scan.py."""
from __future__ import annotations

from pathlib import Path
from unittest import mock

from plugadvpl.scan import MAX_FILE_BYTES, scan_sources


def _touch(path: Path, content: bytes = b"x") -> Path:
    """Cria arquivo com conteúdo dado, criando diretórios se necessário."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


class TestScanSources:
    def test_scans_valid_extensions(self, tmp_path: Path) -> None:
        _touch(tmp_path / "a.prw", b"User Function A() Return\n")
        _touch(tmp_path / "b.tlpp", b"User Function B() Return\n")
        _touch(tmp_path / "c.prx", b"User Function C() Return\n")
        _touch(tmp_path / "d.apw", b"User Function D() Return\n")
        # Não-fontes devem ser ignorados
        _touch(tmp_path / "readme.txt", b"hello")
        _touch(tmp_path / "config.json", b"{}")

        result = scan_sources(tmp_path)
        names = sorted(p.name for p in result)
        assert names == ["a.prw", "b.tlpp", "c.prx", "d.apw"]

    def test_skips_backup_files(self, tmp_path: Path) -> None:
        _touch(tmp_path / "a.prw", b"User Function A() Return\n")
        _touch(tmp_path / "a.prw.bak", b"old content")
        _touch(tmp_path / "b.prw.old", b"older content")
        _touch(tmp_path / "c.prw.tmp", b"temp content")
        _touch(tmp_path / "d.prw~", b"emacs bak")
        _touch(tmp_path / "e.prw.corrupted.bak", b"corrupted")
        _touch(tmp_path / "f.prw.bak2", b"bak2")

        result = scan_sources(tmp_path)
        names = sorted(p.name for p in result)
        # Apenas o "a.prw" cru deve aparecer; todos os outros têm suffix de backup
        assert names == ["a.prw"]

    def test_skips_oversized_files(self, tmp_path: Path) -> None:
        f_big = tmp_path / "big.prw"
        f_small = tmp_path / "small.prw"
        _touch(f_small, b"User Function S() Return\n")
        # Cria arquivo válido mas vamos stub-ar st_size > MAX_FILE_BYTES.
        _touch(f_big, b"User Function B() Return\n")

        real_stat = Path.stat

        def fake_stat(self: Path, *args: object, **kwargs: object) -> object:
            real = real_stat(self, *args, **kwargs)
            if self.name == "big.prw":
                # Simula arquivo gigante via objeto stub.
                class _S:
                    st_size = MAX_FILE_BYTES + 1
                    st_mtime_ns = real.st_mtime_ns

                return _S()
            return real

        with mock.patch.object(Path, "stat", fake_stat):
            result = scan_sources(tmp_path)
        names = sorted(p.name for p in result)
        assert names == ["small.prw"]

    def test_skips_empty_files(self, tmp_path: Path) -> None:
        _touch(tmp_path / "ok.prw", b"User Function A() Return\n")
        _touch(tmp_path / "empty.prw", b"")

        result = scan_sources(tmp_path)
        names = sorted(p.name for p in result)
        assert names == ["ok.prw"]

    def test_dedup_case_insensitive_basename(self, tmp_path: Path) -> None:
        # Em Windows o FS é case-insensitive — não conseguimos criar tanto FATA050.prw
        # quanto FATA050.PRW no mesmo dir. Simulamos os.walk retornando ambos.
        target_file = tmp_path / "FATA050.prw"
        _touch(target_file, b"User Function FATA050() Return\n")

        real_walk = __import__("os").walk

        def fake_walk(top: Path | str) -> object:
            for dirpath, dirnames, filenames in real_walk(top):
                # Adiciona variante uppercase para simular FS case-insensitive listando duplo
                augmented = (
                    [*list(filenames), "FATA050.PRW"]
                    if "FATA050.prw" in filenames
                    else filenames
                )
                yield dirpath, dirnames, augmented

        with mock.patch("plugadvpl.scan.os.walk", fake_walk):
            result = scan_sources(tmp_path)
        names = [p.name for p in result]
        assert len(names) == 1  # Dedup garantido

    def test_skips_plugadvpl_subdir(self, tmp_path: Path) -> None:
        _touch(tmp_path / "real.prw", b"User Function R() Return\n")
        _touch(tmp_path / ".plugadvpl" / "index.db", b"fake-db-content")
        _touch(tmp_path / ".plugadvpl" / "cache.prw", b"User Function C() Return\n")
        # Não fonte ADVPL mesmo — também devemos garantir que nem desceríamos
        _touch(tmp_path / ".git" / "stuff.prw", b"User Function X() Return\n")
        _touch(tmp_path / "node_modules" / "lib.prw", b"User Function Y() Return\n")
        _touch(tmp_path / ".venv" / "lib.prw", b"User Function Z() Return\n")

        result = scan_sources(tmp_path)
        names = sorted(p.name for p in result)
        assert names == ["real.prw"]
