"""Wait for FraudShield VS index and run a sample similarity search."""

from __future__ import annotations

import json
import os
import time

from databricks.vector_search.client import VectorSearchClient


def main() -> int:
  host = os.environ['DATABRICKS_HOST'].rstrip('/')
  token = os.environ['DATABRICKS_TOKEN']
  vsc = VectorSearchClient(
    workspace_url=host if host.startswith('http') else f'https://{host}',
    personal_access_token=token,
    disable_notice=True,
  )
  ep, idx_name = 'fraudshield-vs', 'dev.fraudshield.knowledge_vs_index'

  for i in range(60):
    idx = vsc.get_index(ep, idx_name)
    desc = idx.describe() if hasattr(idx, 'describe') else {}
    blob = json.dumps(desc, default=str)
    print(f'check {i + 1}: {blob[:350]}')
    if 'ONLINE' in blob.upper() or 'READY' in blob.upper():
      try:
        idx.sync()
        print('sync triggered')
      except Exception as e:
        print('sync:', e)
      break
    time.sleep(15)
  else:
    print('WARNING: index not clearly ready after wait')

  for i in range(40):
    try:
      idx = vsc.get_index(ep, idx_name)
      res = idx.similarity_search(
        query_text='steps before confirmed_fraud',
        columns=['id', 'source', 'title', 'text'],
        num_results=3,
      )
      data = (res.get('result') or {}).get('data_array') or res.get('data_array') or []
      print('SEARCH_OK rows=', len(data))
      if data:
        print('first=', data[0][:4] if isinstance(data[0], (list, tuple)) else data[0])
        return 0
      print('empty result, waiting for sync...')
    except Exception as e:
      print(f'search wait {i + 1}: {e}')
    time.sleep(15)

  print('SEARCH_FAILED')
  return 1


if __name__ == '__main__':
  raise SystemExit(main())
