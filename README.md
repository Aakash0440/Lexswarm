# LEXSWARM

> AI legal defense for the 5 billion people who can't afford a lawyer.

[![Python](https://img.shields.io/badge/python-3.11+-blue?style=flat-square)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Languages](https://img.shields.io/badge/languages-100+-orange?style=flat-square)]()
[![Jurisdictions](https://img.shields.io/badge/jurisdictions-100+-purple?style=flat-square)]()
[![Research](https://img.shields.io/badge/paper-ICAIL%202026-red?style=flat-square)]()

You describe your situation in plain language. LEXSWARM identifies your rights, cites the exact statute, simulates how a judge will respond, generates your documents, and alerts a human volunteer lawyer if things are critical — all in your own language, for free.

---

## The problem

- Lawyers cost $200–$500/hour
- US legal aid: 1 lawyer per 6,000 eligible clients
- 5 billion people face legal situations with zero representation
- Existing tools (DoNotPay, Harvey AI) are US-only, expensive, or both

---

## Example

**Input** — in any language:
```
"My landlord changed the locks tonight and threw my belongings outside.
I have nowhere to sleep. This is in Karachi, Pakistan."
```

**Output:**
```
Case: HOUSING  |  Urgency: CRITICAL  |  Country: PK

Your Legal Rights:
  1. Right to adequate notice before eviction
     Law: Rent Restriction Ordinance 2001, Section 15
     → Written notice required. Verbal eviction is illegal.

  2. Protection against illegal lockout
     Law: Transfer of Property Act 1882, Section 108
     → Changing locks without a court order is a criminal offence.

Action Plan:
  Step 1: Call emergency legal aid NOW (within 30 minutes)
  Step 2: Document everything with timestamps
  Step 3: Send the demand letter (within 24 hours)

Courtroom Simulation (MiroFish, 500 agents):
  Win probability: 78%
  Best argument: "Landlord failed to provide adequate notice as required by law"
  Judge will ask: "What specific statute supports this argument?"

Documents generated:
  ✓ Legal Rights Notice (PDF)
  ✓ Demand Letter with statute citations
  ✓ Court Complaint (if no response within 48h)

!! HUMAN LAWYER ALERT SENT — volunteer notified via Telegram !!
```

---

## How it works

```
User input (any language)
         │
    INTAKE LAYER
    Language detection · Jurisdiction detection · Case classifier · Urgency scorer
         │
    FRAMEWORM-SHIFT
    Escalation detection · Human volunteer alert if threshold crossed
         │
    LEGAL KNOWLEDGE LAYER
    CourtListener API · GovInfo API · Offline statute DB (100+ jurisdictions)
    Always cites real statutes — never hallucinates
         │
    MIROFISH COURTROOM SIMULATION
    500 agents: judge, jury, prosecution, defense, opposing counsel
    Win probability per argument · Optimal strategy recommendation
         │
    FRAMEWORM-AGENT
    Demand letters · Court complaints · Rights notices · Action plans
         │
    OUTPUT
    Plain language in user's own language · Downloadable documents · Telegram alert
```

---

## What makes this different

| Feature | DoNotPay | Harvey AI | ChatGPT | **LEXSWARM** |
|---|---|---|---|---|
| 100+ languages | ✗ | ✗ | Partial | **✓** |
| 100+ jurisdictions | ✗ | ✗ | ✗ | **✓** |
| Cites real statutes | ✗ | ✓ | ✗ | **✓** |
| Courtroom simulation | ✗ | ✗ | ✗ | **✓** |
| Crisis escalation detection | ✗ | ✗ | ✗ | **✓** |
| Autonomous document filing | Partial | ✗ | ✗ | **✓** |
| Free for end users | ✗ | ✗ | ✗ | **✓** |

---

## Quickstart

```bash
# Install
pip install httpx transformers torch langdetect \
  python-telegram-bot python-dotenv pyyaml loguru

# Run demo
python scripts/run_lexswarm.py --demo

# Run demo in Urdu
python scripts/run_lexswarm.py --demo --lang ur

# Run your own case
python scripts/run_lexswarm.py --case "My employer hasn't paid my salary for 3 months in Jakarta, Indonesia"
```

---

## Research

**Paper:** *LEXSWARM: Swarm Intelligence and Drift-Aware Agent Systems for Autonomous Legal Defense in Low-Resource Jurisdictions*

Target venues: ICAIL 2026 · ACL 2026 · AAAI 2026 (AI for social good)

**Novelty claims:**
- First system applying swarm agent simulation to courtroom outcome prediction
- First multilingual legal AI covering 100+ jurisdictions simultaneously
- First use of distribution drift detection for legal crisis escalation
- First open-source end-to-end autonomous legal document system for unrepresented populations

---

## Stack

Built on the same FRAMEWORM infrastructure as QUANTSHIFT-SWARM.

`Python 3.11` · `PyTorch` · `Helsinki-NLP multilingual models` · `FRAMEWORM-SHIFT` · `FRAMEWORM-AGENT` · `MiroFish` · `FastAPI` · `Telegram` · `langdetect`

---

> **Disclaimer:** Not a substitute for qualified legal advice. Always review generated documents with a human lawyer before filing. LEXSWARM helps unrepresented people understand their rights and take initial steps — it is not a replacement for legal representation.
>
> MIT © 2026 Aakash Ali
