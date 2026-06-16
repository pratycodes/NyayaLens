# Model Card

## Retrieval Embeddings

Default settings:

```env
EMBEDDING_BACKEND=hash
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

Mock mode uses lightweight hashing retrieval for offline reproducibility. Hashing retrieval is deterministic and does not require model downloads.

Semantic retrieval is available through sentence-transformers after installing optional dependencies:

```bash
make install-optional
```

Then set:

```env
EMBEDDING_BACKEND=sentence-transformers
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

If the model is unavailable, NyayaLens falls back to deterministic hashing rather than requiring a download.

## LLM Provider Abstraction

Provider files:

- `backend/app/llm/base.py`
- `backend/app/llm/mock_provider.py`
- `backend/app/llm/openai_provider.py`

Default:

```env
LLM_PROVIDER=mock
ALLOW_REMOTE_LLM=false
```

OpenAI mode requires optional dependencies plus environment configuration:

```bash
make install-optional
```

```env
OPENAI_API_KEY=...
LLM_PROVIDER=openai
ALLOW_REMOTE_LLM=true
```

## Privacy Mode

If `ALLOW_REMOTE_LLM=false`, private document text is not sent to a remote LLM. Even when `ALLOW_REMOTE_LLM=true`, Streamlit requires per-analysis user consent before remote issue spotting can send document excerpts to the configured provider. The default MVP uses deterministic parsing, issue spotting, rules, retrieval, and templates.

The Overview and Evaluation / Trust tabs show whether the app is in local/mock mode or remote LLM mode is available with consent.

## Training

No local LLM training, fine-tuning, GPU training, or large local model is required.

## Known Limitations

- Mock mode does not understand nuanced legal language beyond rules and keywords.
- Embedding fallback is deterministic but weaker than MiniLM.
- The app should not generate exact legal provisions unless retrieved from source text.
- Demo corpus mode is not a substitute for official legal research.
