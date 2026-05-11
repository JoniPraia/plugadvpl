#!/usr/bin/env node
// hooks/session-start.mjs — plugadvpl SessionStart hook
// Single cross-platform Node.js implementation (replaces bash + cmd duplicates).
// Spec: docs/superpowers/specs/2026-05-11-plugadvpl-design.md §9 + §13.5

import { readdirSync, existsSync } from 'node:fs';
import { join, extname, resolve } from 'node:path';
import { execFileSync } from 'node:child_process';

const VALID_EXTS = new Set(['.prw', '.tlpp', '.prx']);
const MAX_DEPTH = 2;
const SKIP_DIRS = new Set(['.plugadvpl', '.git', 'node_modules', '.venv', '.ruff_cache', '__pycache__', '.benchmarks']);
const ADDITIONAL_CONTEXT_LIMIT = 9500; // Claude Code limit ~10k chars; leave headroom
const FILE_SCAN_LIMIT = 100;            // short-circuit: enough evidence it's ADVPL

function emit(additionalContext) {
  if (!additionalContext) {
    process.exit(0); // silent
  }
  const truncated = additionalContext.slice(0, ADDITIONAL_CONTEXT_LIMIT);
  const out = {
    hookSpecificOutput: {
      hookEventName: 'SessionStart',
      additionalContext: truncated,
    },
  };
  process.stdout.write(JSON.stringify(out));
  process.exit(0);
}

function findAdvplFiles(root, depth = 0, accumulator = []) {
  if (depth > MAX_DEPTH) return accumulator;
  if (accumulator.length >= FILE_SCAN_LIMIT) return accumulator;
  let entries;
  try {
    entries = readdirSync(root, { withFileTypes: true });
  } catch (err) {
    return accumulator; // EACCES, ENOENT, etc — silent fail
  }
  for (const e of entries) {
    if (accumulator.length >= FILE_SCAN_LIMIT) return accumulator;
    if (SKIP_DIRS.has(e.name)) continue;
    if (e.name.startsWith('.') && depth === 0 && !VALID_EXTS.has(extname(e.name).toLowerCase())) {
      // skip dotfiles/dotdirs at root unless they happen to be advpl sources
      continue;
    }
    const full = join(root, e.name);
    if (e.isDirectory()) {
      findAdvplFiles(full, depth + 1, accumulator);
    } else if (e.isFile() && VALID_EXTS.has(extname(e.name).toLowerCase())) {
      accumulator.push(full);
    }
  }
  return accumulator;
}

function checkUvAvailable() {
  try {
    execFileSync('uv', ['--version'], { stdio: 'ignore', timeout: 3000 });
    return true;
  } catch {
    return false;
  }
}

function checkUvxAvailable() {
  try {
    execFileSync('uvx', ['--version'], { stdio: 'ignore', timeout: 3000 });
    return true;
  } catch {
    return false;
  }
}

function checkStaleViaCli(root) {
  try {
    const out = execFileSync(
      'uvx',
      ['plugadvpl@0.1.0', 'status', '--check-stale', '--quiet', '--format', 'json'],
      {
        cwd: root,
        encoding: 'utf-8',
        timeout: 5000,
        stdio: ['ignore', 'pipe', 'ignore'],
      },
    );
    return JSON.parse(out);
  } catch (err) {
    return null; // uvx missing, timeout, or parse error — silent
  }
}

function main() {
  try {
    const root = resolve(process.env.CLAUDE_PROJECT_DIR || process.cwd());

    const advplFiles = findAdvplFiles(root);
    if (advplFiles.length === 0) {
      emit(null); // silent
      return;
    }

    if (!checkUvAvailable() || !checkUvxAvailable()) {
      const isWindows = process.platform === 'win32';
      const installer = isWindows
        ? '  irm https://raw.githubusercontent.com/JoniPraia/plugadvpl/main/scripts/install.ps1 | iex'
        : '  curl -sSL https://raw.githubusercontent.com/JoniPraia/plugadvpl/main/scripts/install.sh | sh';

      emit(
        `Projeto ADVPL detectado (${advplFiles.length}+ fontes) mas \`uv\` não está instalado.\n\n` +
          `O plugadvpl precisa do uv (gerenciador de pacotes Python) para rodar.\n` +
          `Instale com este comando:\n\n` +
          `${installer}\n\n` +
          `Após instalar, abra um terminal NOVO e rode:\n` +
          `  cd "${root}"\n` +
          `  plugadvpl init\n` +
          `  plugadvpl ingest\n\n` +
          `Ou, no Claude Code, rode: /plugadvpl:setup`,
      );
      return;
    }

    const indexDb = join(root, '.plugadvpl', 'index.db');
    if (!existsSync(indexDb)) {
      const countLabel = advplFiles.length >= FILE_SCAN_LIMIT
        ? `${FILE_SCAN_LIMIT}+`
        : String(advplFiles.length);
      emit(
        `Projeto ADVPL detectado (${countLabel} fontes em ${root}).\n` +
          `Para indexar e habilitar consultas eficientes via Claude:\n\n` +
          `  /plugadvpl:init\n` +
          `  /plugadvpl:ingest\n`,
      );
      return;
    }

    // DB exists — check stale + version drift
    const result = checkStaleViaCli(root);
    if (!result) {
      emit(null); // uvx unavailable or status failed — silent
      return;
    }

    const staleN = Array.isArray(result.stale_files) ? result.stale_files.length : 0;
    const versionDrift = Boolean(result.version_drift);

    if (versionDrift) {
      emit(
        'Parser/lookups do plugadvpl foram atualizados desde o último ingest.\n' +
          'Recomendado: /plugadvpl:ingest --no-incremental para reingestir tudo.',
      );
    } else if (staleN > 0) {
      emit(
        `${staleN} arquivos ADVPL modificados desde o último ingest.\n` +
          'Execute /plugadvpl:reindex <arq> ou /plugadvpl:ingest --incremental.',
      );
    } else {
      emit(null); // tudo OK — silent
    }
  } catch (err) {
    // Last-resort silent fail — NEVER break user session
    process.exit(0);
  }
}

main();
