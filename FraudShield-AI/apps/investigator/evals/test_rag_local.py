"""Offline checks for local RAG retrieval (no Databricks required)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running as: python evals/test_rag_local.py from apps/investigator
# Import modules by path to avoid package __init__ pulling mlflow/langchain.
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / 'server' / 'agents' / 'databricks_assistant'


def _load(name: str, path: Path):
  spec = importlib.util.spec_from_file_location(name, path)
  mod = importlib.util.module_from_spec(spec)
  assert spec and spec.loader 
  spec.loader.exec_module(mod)
  return mod


rag_client = _load('rag_client', PKG / 'rag_client.py')

# agent.py imports mlflow; mirror extract helper for offline unit check:
import re
from typing import Any, Dict, List, Set

_TXN_ID_RE = re.compile(
  r'(?:transaction[_ ]?id|txn)\s*[:=#]?\s*([A-Za-z0-9_-]+)|'
  r'\b(\d{6,})\b',
  re.IGNORECASE,
)


def extract_transaction_ids(messages: List[Dict[str, Any]]) -> List[str]:
  found: List[str] = []
  seen: Set[str] = set()
  for msg in messages:
    content = str(msg.get('content') or '')
    for m in _TXN_ID_RE.finditer(content):
      tid = m.group(1) or m.group(2)
      if tid and tid not in seen:
        seen.add(tid)
        found.append(tid)
  return found


retrieve_knowledge = rag_client.retrieve_knowledge


def test_rag_policy_hit():
  result = retrieve_knowledge('steps before marking confirmed_fraud', k=5)
  assert result['hit'] is True, result
  sources = ' '.join(result.get('sources') or [])
  assert 'checklist' in sources or 'hitl' in sources.lower() or any(
    'checklist' in (p.get('source') or '') for p in result['passages']
  ), result


def test_rag_hitl_statuses():
  result = retrieve_knowledge('HITL status confirmed_fraud vs cleared', k=5)
  assert result['hit'] is True, result
  blob = json.dumps(result).lower()
  assert 'confirmed_fraud' in blob or 'cleared' in blob


def test_txn_memory_extraction():
  msgs = [
    {'role': 'user', 'content': 'Look at transaction_id 998877'},
    {'role': 'assistant', 'content': 'Found score 0.95'},
    {'role': 'user', 'content': 'investigate that transaction'},
  ]
  ids = extract_transaction_ids(msgs)
  assert '998877' in ids


def main() -> int:
  golden = json.loads((Path(__file__).parent / 'golden_questions.json').read_text(encoding='utf-8'))
  failures = 0
  for case in golden:
    if case.get('type') != 'rag':
      continue
    result = retrieve_knowledge(case['question'], k=5)
    ok = result.get('hit') is True
    if case.get('expect_source_substrings'):
      blob = json.dumps(result).lower()
      ok = ok and any(s.lower() in blob for s in case['expect_source_substrings'])
    status = 'PASS' if ok else 'FAIL'
    print(f'{status} {case["id"]}: hit={result.get("hit")} sources={result.get("sources")}')
    if not ok:
      failures += 1

  test_rag_policy_hit()
  test_rag_hitl_statuses()
  test_txn_memory_extraction()
  print('unit checks passed')
  return 1 if failures else 0


if __name__ == '__main__':
  raise SystemExit(main())
