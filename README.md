# LEXSWARM — AI Legal Defense System for the Unrepresented

> 5 billion people have no access to a lawyer. LEXSWARM gives everyone the same quality of legal defense that money currently buys — in any language, any jurisdiction, for free.

## The problem

- Lawyers cost $200–$500/hour
- Legal aid offices have 1 lawyer per 6,000 eligible clients (US)
- 5 billion people worldwide face legal situations with zero representation
- Existing tools (DoNotPay, Harvey AI) are US-only, expensive, or inaccessible

## What LEXSWARM does

You describe your situation in any language. LEXSWARM:

1. Detects your language, jurisdiction, and case type automatically
2. Identifies your exact legal rights with real statute citations
3. Simulates how a judge, jury, and opposing counsel will react to your arguments (MiroFish courtroom simulation)
4. Detects if your situation is escalating into a crisis (FRAMEWORM-SHIFT)
5. Generates demand letters, rights notices, and court complaints instantly
6. Alerts a human volunteer lawyer if the situation is critical

**Sample input:**
```
"My landlord changed the locks tonight and threw my belongings outside. I have nowhere to sleep. This is in Karachi, Pakistan."
```

**Sample output:**
```
Case: HOUSING | Urgency: CRITICAL | Country: PK

Your Legal Rights:
1. Right to adequate notice before eviction
   Law: Rent Restriction Ordinance 2001, Section 15
   Meaning: Your landlord must give written notice. Verbal eviction is illegal.

2. Protection against illegal lockout
   Law: Transfer of Property Act 1882, Section 108
   Meaning: Changing locks without a court order is a criminal offence.

Action Plan:
  Step 1: Call emergency legal aid NOW (within 30 minutes)
  Step 2: Document everything with timestamps (immediately)
  Step 3: Send the demand letter (within 24 hours)

Courtroom Simulation:
  Win probability: 78%
  Best argument: "Landlord failed to provide adequate notice as required by law"
  Judge will ask: "What specific statute supports this argument?"

Documents generated:
  - Legal Rights Notice (PDF ready)
  - Demand Letter with statute citations (fill in brackets, send tonight)
  - Court Complaint (if no response within 48h)

!! HUMAN LAWYER ALERT SENT — volunteer notified via Telegram !!
```

## Architecture

```
User input (any language)
        |
   INTAKE LAYER
   - Language detection (100+ languages)
   - Jurisdiction detector
   - Case type classifier
   - Urgency scorer
        |
   FRAMEWORM-SHIFT (escalation detector)
   - Detects crisis escalation patterns
   - Alerts human volunteer if threshold crossed
        |
   LEGAL KNOWLEDGE LAYER
   - CourtListener API (free, US case law)
   - GovInfo API (US federal law)
   - Offline statute database (100+ jurisdictions)
   - Always cites real statutes — never hallucinates
        |
   MIROFISH COURTROOM SIMULATION
   - 500 agents: judge, jury, prosecution, defense, opposing counsel
   - Predicts favorable probability per argument
   - Recommends optimal legal strategy
        |
   FRAMEWORM-AGENT (document generation)
   - Demand letters
   - Court complaints
   - Rights notices
   - Step-by-step action plans
        |
   OUTPUT
   - Plain language in user's own language
   - Downloadable documents
   - Human lawyer alert via Telegram
```

## What makes this never-been-done

| Feature | DoNotPay | Harvey AI | ChatGPT | LEXSWARM |
|---------|----------|-----------|---------|---------|
| 100+ languages | No | No | Partial | Yes |
| 100+ jurisdictions | No | No | No | Yes |
| Cites real statutes | No | Yes | No | Yes |
| Courtroom simulation | No | No | No | Yes (MiroFish) |
| Crisis escalation detection | No | No | No | Yes (FRAMEWORM) |
| Autonomous document filing | Partial | No | No | Yes (AGENT) |
| Free for end users | No | No | No | Yes |

## Quick start

```bash
# Install
pip install httpx transformers torch langdetect python-telegram-bot python-dotenv pyyaml loguru

# Run demo
set PYTHONPATH=.
python scripts/run_lexswarm.py --demo

# Run demo in Urdu
python scripts/run_lexswarm.py --demo --lang ur

# Run your own case
python scripts/run_lexswarm.py --case "My employer has not paid my salary for 3 months in Jakarta, Indonesia"
```

## Research targets

- ACL 2026 — multilingual legal NLP
- AAAI 2026 — AI for social good track
- ICAIL 2026 — International Conference on AI and Law

**Paper title:** *LEXSWARM: Swarm Intelligence and Drift-Aware Agent Systems for Autonomous Legal Defense in Low-Resource Jurisdictions*

## Novelty claims

1. First system to apply swarm agent simulation to courtroom outcome prediction
2. First multilingual legal AI covering 100+ jurisdictions simultaneously
3. First application of distribution drift detection to legal crisis escalation
4. First open-source end-to-end autonomous legal document system for unrepresented populations

## Built with

Same FRAMEWORM stack as QUANTSHIFT-SWARM:
- Python 3.11+ | PyTorch | Transformers (Helsinki-NLP multilingual models)
- FRAMEWORM-SHIFT (drift/escalation detection)
- MiroFish (swarm agent simulation)
- FRAMEWORM-AGENT (autonomous document generation)
- FastAPI | Telegram | langdetect

---

*Not a substitute for qualified legal advice. Always review generated documents with a human lawyer before filing. LEXSWARM is a tool to help unrepresented people understand their rights and take initial action — not a replacement for legal representation.*

**github.com/Aakash0440/lexswarm**
