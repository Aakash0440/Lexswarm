# scripts/run_lexswarm.py
# LEXSWARM main pipeline — takes a case description, runs full analysis
# Usage:
#   python scripts/run_lexswarm.py
#   python scripts/run_lexswarm.py --lang ur --demo
#   python scripts/run_lexswarm.py --case "My landlord locked me out tonight in Karachi"

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import argparse
from dotenv import load_dotenv
load_dotenv()

from intake.classifier import CaseClassifier
from intake.translator import MultilingualTranslator
from knowledge.retriever import LegalKnowledgeRetriever
from regime.escalation_detector import EscalationDetector
from simulation.courtroom_swarm import CourtroomSwarm
from agent.document_generator import LegalDocumentGenerator
from alerts.volunteer_alert import VolunteerAlerter
from intake.base import UrgencyLevel


DEMO_CASES = {
    "en": "My landlord changed the locks tonight and threw my belongings outside. I have nowhere to sleep. This is in Karachi, Pakistan.",
    "ur": "میرے مالک مکان نے آج رات تالہ بدل دیا اور میرا سامان باہر پھینک دیا۔ مجھے سونے کی جگہ نہیں ہے۔",
    "id": "Majikan saya tidak membayar gaji saya selama 3 bulan dan mengancam akan memecat saya jika saya mengeluh.",
    "crisis": "Police arrested me without showing any warrant. They are holding me at the station. I have not been told what I am charged with.",
}


async def run_case(description: str, demo_mode: bool = False) -> dict:
    """Run full LEXSWARM pipeline on a case description."""

    print("\n" + "="*60)
    print("LEXSWARM — AI Legal Defense System")
    print("="*60 + "\n")

    # ── STEP 1: Intake & Classification ───────────────────────────────────────
    print("Step 1: Analyzing your situation...")
    classifier = CaseClassifier()
    case = classifier.intake(description)
    print(f"  Case ID:       {case.case_id}")
    print(f"  Case type:     {case.case_type.value}")
    print(f"  Urgency:       {case.urgency.name}")
    print(f"  Country:       {case.country}")
    print(f"  Language:      {case.language}")

    # ── STEP 2: Translation ────────────────────────────────────────────────────
    if case.language != "en":
        print(f"\nStep 2: Translating from {case.language} to English...")
        translator = MultilingualTranslator()
        result = translator.translate(description, case.language)
        case.translated_description = result.translated_text
        print(f"  Translation: {case.translated_description[:100]}...")
    else:
        case.translated_description = description
        print("\nStep 2: Language is English — no translation needed")

    # ── STEP 3: Escalation Detection (FRAMEWORM-SHIFT) ────────────────────────
    print("\nStep 3: Assessing urgency and crisis level...")
    detector = EscalationDetector()
    escalation = detector.detect(case)
    case.escalation_score = escalation.escalation_score
    case.urgency = escalation.urgency
    print(f"  Escalation score: {escalation.escalation_score:.0%}")
    print(f"  Final urgency:    {escalation.urgency.name}")
    print(f"  Requires human:   {escalation.requires_human}")
    if escalation.triggers:
        print(f"  Triggers:         {', '.join(escalation.triggers[:3])}")
    print(f"  Response needed:  within {escalation.recommended_response_hours}h")

    # ── STEP 4: Legal Knowledge Retrieval ─────────────────────────────────────
    print("\nStep 4: Retrieving relevant laws and rights...")
    retriever = LegalKnowledgeRetriever()
    case.legal_rights = await retriever.retrieve(case)
    print(f"  Found {len(case.legal_rights)} relevant rights and statutes")
    for right in case.legal_rights[:3]:
        print(f"  - {right.statute[:60]}")
    await retriever.close()

    # ── STEP 5: Courtroom Simulation (MiroFish) ────────────────────────────────
    print("\nStep 5: Simulating courtroom outcomes...")
    swarm = CourtroomSwarm(n_agents_per_type=100)
    sim_result = swarm.simulate(case, mock=True)
    case.simulation_result = {
        "win_probability": sim_result.overall_win_probability,
        "strategy": sim_result.recommended_strategy,
        "best_argument": sim_result.key_arguments[0].argument if sim_result.key_arguments else "",
    }
    print(f"  Overall win probability: {sim_result.overall_win_probability:.0%}")
    print(f"  Best argument: {sim_result.key_arguments[0].argument[:70] if sim_result.key_arguments else 'N/A'}")

    # ── STEP 6: Document Generation (FRAMEWORM-AGENT) ─────────────────────────
    print("\nStep 6: Generating legal documents...")
    generator = LegalDocumentGenerator()
    case.recommended_actions = generator.build_action_plan(case)
    case.generated_documents = generator.generate_all_documents(case)
    print(f"  Generated {len(case.generated_documents)} document(s):")
    for doc in case.generated_documents:
        print(f"  - {doc.title}")

    # ── STEP 7: Human Alert if needed ─────────────────────────────────────────
    if escalation.requires_human:
        print("\nStep 7: Alerting volunteer lawyers...")
        alerter = VolunteerAlerter()
        await alerter.alert(case, escalation)
    else:
        print("\nStep 7: No human escalation required for this case")

    # ── OUTPUT ─────────────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("LEXSWARM ANALYSIS COMPLETE")
    print("="*60)

    print(f"\nCASE {case.case_id} — {case.case_type.value.upper()}")
    print(f"Urgency: {case.urgency.name} | Country: {case.country}\n")

    print("YOUR LEGAL RIGHTS:")
    for i, right in enumerate(case.legal_rights[:4], 1):
        print(f"  {i}. {right.right}")
        print(f"     Law: {right.statute}")
        print(f"     Plain English: {right.plain_english}\n")

    print("RECOMMENDED ACTION PLAN:")
    for action in case.recommended_actions:
        print(f"  Step {action.step_number}: {action.action}")
        print(f"           When: {action.deadline}")
        print(f"           How:  {action.how_to[:100]}")
        if action.requires_human:
            print(f"           ** This step requires a human lawyer **")
        print()

    print("COURTROOM SIMULATION:")
    print(f"  Win probability: {sim_result.overall_win_probability:.0%}")
    print(f"  Strategy: {sim_result.recommended_strategy[:150]}")
    if sim_result.judge_likely_concerns:
        print(f"  Judge will ask: {sim_result.judge_likely_concerns[0]}")
    print()

    print("GENERATED DOCUMENTS:")
    for doc in case.generated_documents:
        print(f"\n{'─'*50}")
        print(f"  {doc.title.upper()}")
        print(f"{'─'*50}")
        print(doc.content[:600] + "\n  [... full document generated ...]\n")

    if escalation.requires_human:
        print("!! HUMAN LAWYER ALERT SENT !!")
        print("   A volunteer lawyer has been notified of your case.")
        print("   You should expect contact within the recommended response window.\n")

    return {"case": case, "simulation": sim_result, "escalation": escalation}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LEXSWARM Legal Defense System")
    parser.add_argument("--case", default=None, help="Case description text")
    parser.add_argument("--demo", action="store_true", help="Run demo case")
    parser.add_argument("--lang", default="en", choices=list(DEMO_CASES.keys()), help="Demo language")
    args = parser.parse_args()

    if args.demo or args.case is None:
        description = DEMO_CASES.get(args.lang, DEMO_CASES["en"])
        print(f"Running demo case ({args.lang}):\n{description}\n")
    else:
        description = args.case

    asyncio.run(run_case(description, demo_mode=args.demo))
