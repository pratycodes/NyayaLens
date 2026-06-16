# Model Card

## Embeddings

Default embedding setting:

```env
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

The app attempts cached local loading only. If the model is unavailable, NyayaLens falls back to deterministic hashing embeddings so mock mode still works without network downloads.

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

OpenAI mode requires:

```env
OPENAI_API_KEY=...
LLM_PROVIDER=openai
ALLOW_REMOTE_LLM=true
```

## Privacy Mode

If `ALLOW_REMOTE_LLM=false`, private document text is not sent to a remote LLM. The MVP uses deterministic parsing, issue spotting, rules, retrieval, and templates.

## Training

No local LLM training, fine-tuning, GPU training, or large local model is required.

## Known Limitations

- Mock mode does not understand nuanced legal language beyond rules and keywords.
- Embedding fallback is deterministic but weaker than MiniLM.
- The app should not generate exact legal provisions unless retrieved from source text.
