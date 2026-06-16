# Safety

## Legal Information Only

NyayaLens provides legal information for education and issue spotting. It is not legal advice and does not create a lawyer-client relationship.

## Privacy And Local Storage

Mock mode keeps analysis local. Remote LLM mode requires both environment configuration and a per-analysis user consent checkbox in the Streamlit UI before document excerpts may be sent to an API provider.

Uploaded files are stored locally only. The default local-demo upload limit is 10 MB, Streamlit parser temp files are deleted after parsing, and backend uploads can be cleared with `make clean-local`.

## Unsafe Request Categories

NyayaLens refuses requests involving:

- forged documents or fake notices
- threats or blackmail
- impersonation
- harassment
- illegal lock-breaking
- unlawful self-help eviction
- destroying or fabricating evidence
- illegally bypassing notice obligations

Blocking safety checks inspect only the user's active intent, such as the plain-text dispute description or follow-up chat message. They do not scan uploaded document text, retrieved corpus chunks, generated disclaimers, extracted clauses, or audit traces for refusal triggers.

Victim/reporting contexts such as "my employer is harassing me" or "I am being threatened" should not be refused. They may still trigger legal-aid or human-review suggestions.

## Hallucination Prevention

The verifier checks that:

- a disclaimer is present
- exact legal section claims are supported by retrieved text
- jurisdiction is not overclaimed
- outcome guarantees are absent
- missing facts are listed
- unsafe requests are refused

If verification fails, the report includes:

```text
Not enough verified source material was found to answer confidently.
```

## Citation Policy

Legal claims should be tied to retrieved local sources or marked as general information. The app must not invent statutes, sections, judgments, portals, or guaranteed outcomes.

## Human Escalation

High-risk clauses, withheld wages, threatened eviction, harassment, and large monetary deductions should be escalated to qualified lawyers, legal aid clinics, labour offices, or appropriate local rent/civil authorities depending on the state and facts.

The Evaluation / Trust tab surfaces human-review signals such as high severity risks, unclear jurisdiction, arbitration clauses, safety-sensitive issues, and demo-corpus-only retrieval.
