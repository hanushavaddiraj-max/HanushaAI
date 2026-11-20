"""FraudShield RAG retrieval: Vector Search when configured, else local knowledge fallback."""

from __future__ import annotations

import json
import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _knowledge_dirs() -> List[Path]:
  """Resolve bundled knowledge folders (app package + monorepo)."""
  here = Path(__file__).resolve()
  env_dir = os.getenv('FRAUDSHIELD_KNOWLEDGE_DIR', '').strip()
  candidates = [
    here.parents[3] / 'knowledge',  # apps/investigator/knowledge
    here.parents[5] / 'knowledge' if len(here.parents) > 5 else None,  # FraudShield-AI/knowledge
    Path(env_dir) if env_dir else None,
  ]
  out: List[Path] = []
  seen = set()
  for c in candidates:
    if not c:
      continue
    try:
      resolved = c.resolve()
    except OSError:
      continue
    if resolved.is_dir() and resolved not in seen:
      seen.add(resolved)
      out.append(resolved)
  return out


@lru_cache(maxsize=1)
def _load_local_chunks() -> List[Dict[str, str]]:
  chunks: List[Dict[str, str]] = []
  for d in _knowledge_dirs():
    for path in sorted(d.glob('*.md')):
      text = path.read_text(encoding='utf-8')
      parts = re.split(r'\n(?=#{1,3}\s)', text.strip())
      title_default = path.stem.replace('_', ' ').title()
      for part in parts:
        part = part.strip()
        if len(part) < 40:
          continue
        heading = title_default
        m = re.match(r'^(#{1,3})\s+(.+)', part)
        if m:
          heading = m.group(2).strip()
        chunks.append({'source': path.name, 'title': heading, 'text': part[:1200]})
  logger.info('Loaded %s local knowledge chunks from %s', len(chunks), _knowledge_dirs())
  return chunks


def _tokenize_score(query: str, text: str) -> float:
  q = {t for t in re.findall(r'[a-z0-9_]+', query.lower()) if len(t) > 2}
  if not q:
    return 0.0
  doc = text.lower()
  hits = sum(1 for t in q if t in doc)
  return hits / len(q)


def _local_retrieve(query: str, k: int) -> List[Dict[str, Any]]:
  scored = []
  for ch in _load_local_chunks():
    s = _tokenize_score(query, ch['text'] + ' ' + ch['title'])
    if s > 0:
      scored.append({**ch, 'score': round(s, 4), 'backend': 'local_knowledge'})
  scored.sort(key=lambda r: r['score'], reverse=True)
  return scored[:k]


def vs_endpoint() -> Optional[str]:
  return os.getenv('FRAUDSHIELD_VS_ENDPOINT') or None


def vs_index() -> Optional[str]:
  return os.getenv('FRAUDSHIELD_VS_INDEX') or None


def embedding_endpoint() -> str:
  return os.getenv('FRAUDSHIELD_EMBEDDING_ENDPOINT', 'databricks-gte-large-en')


def _workspace_host() -> str:
  host = (os.getenv('DATABRICKS_HOST') or '').rstrip('/')
  if host:
    return host if host.startswith('http') else f'https://{host}'
  try:
    from databricks.sdk import WorkspaceClient

    h = (WorkspaceClient().config.host or '').rstrip('/')
    if h:
      return h if h.startswith('http') else f'https://{h}'
  except Exception:
    pass
  return ''


def _vector_search_client():
  """Auth for Apps (SP) or local (PAT)."""
  from databricks.vector_search.client import VectorSearchClient

  host = _workspace_host()
  client_id = os.getenv('DATABRICKS_CLIENT_ID')
  client_secret = os.getenv('DATABRICKS_CLIENT_SECRET')
  token = os.getenv('DATABRICKS_TOKEN')
  if not token:
    try:
      from databricks.sdk import WorkspaceClient

      token = WorkspaceClient().config.token
    except Exception:
      token = None

  if host and client_id and client_secret:
    return VectorSearchClient(
      workspace_url=host,
      service_principal_client_id=client_id,
      service_principal_client_secret=client_secret,
      disable_notice=True,
    )
  if host and token:
    return VectorSearchClient(
      workspace_url=host,
      personal_access_token=token,
      disable_notice=True,
    )
  raise RuntimeError(
    'Vector Search needs host + (DATABRICKS_TOKEN or CLIENT_ID/SECRET)'
  )


def _vector_search_retrieve(query: str, k: int) -> List[Dict[str, Any]]:
  endpoint = vs_endpoint()
  index = vs_index()
  if not endpoint or not index:
    raise RuntimeError('FRAUDSHIELD_VS_ENDPOINT / FRAUDSHIELD_VS_INDEX not set')

  vsc = _vector_search_client()
  idx = vsc.get_index(endpoint, index)
  result = idx.similarity_search(
    query_text=query,
    columns=['id', 'source', 'title', 'text'],
    num_results=k,
  )
  # result['result']['data_array'] is list of rows matching columns + score
  data = result.get('result', {}).get('data_array') or result.get('data_array') or []
  cols = ['id', 'source', 'title', 'text', 'score']
  rows: List[Dict[str, Any]] = []
  for raw in data:
    values = list(raw) if not isinstance(raw, dict) else [raw.get(c) for c in cols]
    item = {
      'id': values[0] if len(values) > 0 else None,
      'source': values[1] if len(values) > 1 else 'unknown',
      'title': values[2] if len(values) > 2 else '',
      'text': values[3] if len(values) > 3 else '',
      'score': values[4] if len(values) > 4 else None,
      'backend': 'vector_search',
    }
    rows.append(item)
  return rows


def retrieve_knowledge(query: str, k: int = 5) -> Dict[str, Any]:
  """Retrieve investigation knowledge passages for a natural-language query."""
  k = max(1, min(int(k), 10))
  query = (query or '').strip()
  if not query:
    return {'hit': False, 'passages': [], 'message': 'Empty query'}

  passages: List[Dict[str, Any]] = []
  backend = 'none'
  error: Optional[str] = None

  if vs_endpoint() and vs_index():
    try:
      passages = _vector_search_retrieve(query, k)
      backend = 'vector_search'
    except Exception as e:
      error = str(e)
      logger.warning('Vector Search retrieve failed, falling back to local: %s', e)

  if not passages:
    passages = _local_retrieve(query, k)
    backend = 'local_knowledge' if passages else backend

  sources = sorted({p.get('source') or 'unknown' for p in passages})
  return {
    'hit': bool(passages),
    'backend': backend,
    'query': query,
    'sources': sources,
    'passages': passages,
    'fallback_error': error,
    'message': None
    if passages
    else 'No knowledge passages found. Do not invent policy; say the playbook had no match.',
  }


def retrieve_knowledge_json(query: str, k: int = 5) -> str:
  return json.dumps(retrieve_knowledge(query, k), default=str, indent=2)
