"""FraudShield LangChain investigation agent."""

import logging
import re
from typing import Any, Dict, List, Optional, Set

import mlflow
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_models import ChatDatabricks
from openai.types.chat import ChatCompletionMessageParam

from .tools import create_fraud_tools

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are FraudShield AI, a fraud investigation assistant for human analysts.

You help investigate synthetic financial transactions using ONLY evidence returned by your tools.
You do not invent transaction ids, scores, merchants, customer history, or policy text.

Tool routing:
- SQL / data tools → live facts: scores, gold rows, customer history, risk evidence, HITL writes.
- retrieve_investigation_knowledge (RAG) → playbooks: checklist, HITL statuses, MCC/amount heuristics, report SOP.
- Never use RAG as a substitute for fraud_predictions or gold tables.
- Never use SQL tools to answer pure policy questions when RAG is available.

Capabilities (via tools):
- List high-risk transactions from ML prediction history
- Fetch transaction details from gold tables
- Fetch model prediction metadata (score, model version, scored_at)
- Customer transaction history and risk profile
- Risk evidence indicators (not proof of fraud)
- Retrieve investigation knowledge (RAG playbooks)
- Generate investigation report drafts for human review
- Record analyst HITL review status (never auto-enforce)

Rules:
1. Always call tools before answering factual questions about transactions or scores.
2. For policy / procedure / "what should I do before confirmed_fraud" questions, call retrieve_investigation_knowledge first.
3. Cite transaction_id, fraud_score, model_version, and scored_at when available.
4. When RAG is used, end with a line: Sources: <filename1>, <filename2>
5. Distinguish predicted risk from confirmed fraud labels (is_fraud may lag or be training-only).
6. Never claim correlation proves fraud. Heuristics are indicators only.
7. Never block cards, freeze accounts, or mark someone a confirmed fraudster by yourself.
   Recording status requires explicit analyst intent; prefer cleared/in_review/escalated language carefully.
8. If SQL tools return no rows or errors, say so clearly — do not invent data.
9. If RAG returns hit=false / no passages, say the playbook had no match — do not invent policy.
10. Keep answers structured and analyst-friendly (bullets / short sections).
11. Multi-turn: if the user says "that transaction" / "investigate it" and a transaction_id appeared earlier, reuse that id.
"""


def format_messages_for_langchain(
  messages: List[ChatCompletionMessageParam],
) -> List[Dict[str, Any]]:
  """Convert OpenAI message format to LangChain format."""
  formatted_messages = []
  for msg in messages:
    role = msg.get('role', 'user')
    content = msg.get('content', '')

    if role == 'system':
      continue
    elif role == 'assistant':
      formatted_messages.append({'role': 'assistant', 'content': content})
    else:
      formatted_messages.append({'role': 'human', 'content': content})

  return formatted_messages


_TXN_ID_RE = re.compile(
  r'(?:transaction[_ ]?id|txn)\s*[:=#]?\s*([A-Za-z0-9_-]+)|'
  r'\b(\d{6,})\b',
  re.IGNORECASE,
)


def extract_transaction_ids(messages: List[ChatCompletionMessageParam]) -> List[str]:
  """Pull transaction ids mentioned across the conversation for multi-turn continuity."""
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


def _ensure_sources_footer(text: str, sources: List[str]) -> str:
  if not sources:
    return text
  if re.search(r'(?im)^sources\s*:', text):
    return text
  return text.rstrip() + '\n\nSources: ' + ', '.join(sources)


def _collect_sources_from_steps(intermediate_steps: Any) -> List[str]:
  sources: List[str] = []
  seen: Set[str] = set()
  if not intermediate_steps:
    return sources
  for step in intermediate_steps:
    try:
      _action, observation = step
    except Exception:
      continue
    obs = observation if isinstance(observation, str) else str(observation)
    if 'retrieve_investigation_knowledge' in str(getattr(_action, 'tool', '')) or (
      '"sources"' in obs and 'passages' in obs
    ):
      # Parse source filenames from JSON-ish observation
      for m in re.finditer(r'[\w\-]+\.md', obs):
        name = m.group(0)
        if name not in seen:
          seen.add(name)
          sources.append(name)
  return sources


def _rag_hit_from_steps(intermediate_steps: Any) -> bool:
  if not intermediate_steps:
    return False
  for step in intermediate_steps:
    try:
      action, observation = step
    except Exception:
      continue
    tool = str(getattr(action, 'tool', '') or '')
    obs = observation if isinstance(observation, str) else str(observation)
    if 'retrieve_investigation_knowledge' in tool or (
      '"hit": true' in obs.replace(' ', '').lower() or '"hit":true' in obs.replace(' ', '')
    ):
      if 'retrieve_investigation_knowledge' in tool or 'passages' in obs:
        if '"hit": false' in obs.lower().replace(' ', '') or '"hit":false' in obs.replace(' ', ''):
          if 'retrieve_investigation_knowledge' in tool:
            return False
          continue
        return True
  return False


@mlflow.trace(span_type='LLM')
def databricks_agent(messages: List[ChatCompletionMessageParam]) -> Dict[str, Any]:
  """Fraud investigation agent with UC/SQL + RAG knowledge tools."""
  llm = ChatDatabricks(
    endpoint='databricks-llama-4-maverick',
    max_tokens=1600,
    temperature=0.1,
  )

  prompt = ChatPromptTemplate.from_messages(
    [
      ('system', SYSTEM_PROMPT),
      MessagesPlaceholder(variable_name='messages'),
      MessagesPlaceholder(variable_name='agent_scratchpad'),
    ]
  )

  tools = create_fraud_tools()
  agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
  agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    return_intermediate_steps=True,
  )

  formatted_messages = format_messages_for_langchain(messages)
  user_messages = [msg for msg in messages if msg.get('role') == 'user']
  if not user_messages:
    return {
      'choices': [
        {'message': {'role': 'assistant', 'content': 'Please provide an investigation question.'}}
      ],
      'sources': [],
      'rag_hit': False,
    }

  last_user_message = str(user_messages[-1].get('content', ''))
  txn_ids = extract_transaction_ids(messages)
  # Soft memory hint for pronouns / "that transaction"
  if txn_ids and re.search(
    r'\b(that|this|the)\s+(transaction|txn|one)\b|\binvestigate\s+it\b',
    last_user_message,
    re.I,
  ):
    last_user_message = (
      f'{last_user_message}\n\n[Context: most recently mentioned transaction_id={txn_ids[-1]}]'
    )

  try:
    result = agent_executor.invoke(
      {
        'messages': formatted_messages,
        'input': last_user_message,
      }
    )
    content = result.get('output', 'I encountered an error processing your request.')
    steps = result.get('intermediate_steps')
    sources = _collect_sources_from_steps(steps)
    rag_hit = _rag_hit_from_steps(steps) or bool(sources)
    content = _ensure_sources_footer(content, sources)

    try:
      mlflow.update_current_trace(
        tags={
          'rag_hit': 'true' if rag_hit else 'false',
          'rag_sources': ','.join(sources) if sources else '',
          'txn_context': txn_ids[-1] if txn_ids else '',
        }
      )
    except Exception as tag_err:
      logger.debug('MLflow tag update skipped: %s', tag_err)

    return {
      'choices': [{'message': {'role': 'assistant', 'content': content}}],
      'sources': sources,
      'rag_hit': rag_hit,
    }
  except Exception as e:
    logger.error(f'Error in agent execution: {str(e)}')
    try:
      mlflow.update_current_trace(tags={'rag_hit': 'false', 'agent_error': 'true'})
    except Exception:
      pass
    return {
      'choices': [
        {'message': {'role': 'assistant', 'content': f'I encountered an error: {str(e)}'}}
      ],
      'sources': [],
      'rag_hit': False,
    }
