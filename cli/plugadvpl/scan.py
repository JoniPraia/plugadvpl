"""Descoberta de arquivos ADVPL/TLPP no projeto cliente.

Usa ``os.walk`` (1 traversal) em vez de ``Path.rglob`` (N traversals por padrão),
aplicando filtros de extensão, dedup case-insensitive e limites de tamanho.
"""
from __future__ import annotations

import os
from pathlib import Path

VALID_EXTENSIONS = frozenset({".prw", ".tlpp", ".prx", ".apw"})

# Sufixos de backup tipicamente gerados por editores e ferramentas Protheus.
# Match case-sensitive — backup tools usualmente preservam o sufixo literal.
SKIP_SUFFIXES = (".bak", ".corrupted.bak", ".old", ".bak2", ".tmp", "~")

# Limite superior — fontes ADVPL legítimos raramente passam de ~500KB.
# Acima de 5MB é quase certo lixo (binário renomeado, dump, etc.).
MAX_FILE_BYTES = 5_000_000

# Diretórios ignorados durante descida (não-source ou nosso próprio índice).
_SKIP_DIRS = frozenset({".plugadvpl", ".git", "node_modules", ".venv"})


def scan_sources(root: Path) -> list[Path]:
    """Scan ``root`` recursivamente listando fontes ADVPL/TLPP.

    Aplica:

    - Filtro de extensão case-insensitive contra :data:`VALID_EXTENSIONS`.
    - Skip de sufixos de backup (.bak, .corrupted.bak, .old, .bak2, .tmp, ~).
    - Skip de arquivos vazios (0 bytes) e oversized (>5MB).
    - Dedup case-insensitive sobre basename — Windows pode reportar ``.PRW`` e
      ``.prw`` da mesma entrada; mantém o primeiro encontrado.
    - Skip de subdiretórios ``.plugadvpl/``, ``.git/``, ``node_modules/``, ``.venv/``.

    Retorna lista ordenada por basename lowercase (determinístico, independente
    de ordem do filesystem).
    """
    files: list[Path] = []
    seen_keys: set[str] = set()

    for dirpath, dirnames, filenames in os.walk(root):
        # Mutate dirnames in-place para que os.walk pule esses subdirs (não desce neles).
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]

        for fname in filenames:
            # Backup suffix — endswith case-sensitive
            if any(fname.endswith(suf) for suf in SKIP_SUFFIXES):
                continue

            # Extension filter — case-insensitive
            ext = Path(fname).suffix.lower()
            if ext not in VALID_EXTENSIONS:
                continue

            full = Path(dirpath) / fname
            try:
                size = full.stat().st_size
            except OSError:
                # Permissão negada / link quebrado / race entre walk e stat — pula.
                continue
            if size == 0 or size > MAX_FILE_BYTES:
                continue

            # Dedup case-insensitive sobre basename
            key = fname.lower()
            if key in seen_keys:
                continue
            seen_keys.add(key)
            files.append(full)

    return sorted(files, key=lambda p: p.name.lower())
