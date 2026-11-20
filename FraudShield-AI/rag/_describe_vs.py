import json
import os
from databricks.vector_search.client import VectorSearchClient

host = os.environ['DATABRICKS_HOST'].rstrip('/')
token = os.environ['DATABRICKS_TOKEN']
vsc = VectorSearchClient(
  workspace_url=host if host.startswith('http') else f'https://{host}',
  personal_access_token=token,
  disable_notice=True,
)
idx = vsc.get_index('fraudshield-vs', 'dev.fraudshield.knowledge_vs_index')
desc = idx.describe()
print(json.dumps(desc, indent=2, default=str))
