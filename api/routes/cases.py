# api/routes/cases.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from api.models import CaseRequest, CaseResponse, LegalRightResponse, ActionResponse, DocumentResponse, SimulationResponse

router = APIRouter()
_case_store: dict = {}   # in-memory store — swap for Redis/DB in production


@router.post("/analyze", response_model=CaseResponse, tags=["Cases"])
async def analyze_case(request: CaseRequest):
    """
    Full LEXSWARM pipeline:
    1. Classify case (language, jurisdiction, type, urgency)
    2. Retrieve relevant statutes
    3. Detect escalation (FRAMEWORM-SHIFT)
    4. Simulate courtroom outcomes (MiroFish)
    5. Generate legal documents (FRAMEWORM-AGENT)
    6. Alert human volunteer if CRITICAL
    """
    try:
        from intake.classifier import CaseClassifier
        from intake.translator import MultilingualTranslator
        from knowledge.retriever import LegalKnowledgeRetriever
        from regime.escalation_detector import EscalationDetector
        from simulation.courtroom_swarm import CourtroomSwarm
        from agent.document_generator import LegalDocumentGenerator
        from alerts.volunteer_alert import VolunteerAlerter

        # Step 1: Classify
        classifier = CaseClassifier()
        case = classifier.intake(request.description)
        if request.country_hint:
            case.country = request.country_hint

        # Step 2: Translate if needed
        if case.language != "en":
            translator = MultilingualTranslator()
            result = translator.translate(request.description, case.language)
            case.translated_description = result.translated_text

        # Step 3: Escalation detection
        detector = EscalationDetector()
        escalation = detector.detect(case)
        case.escalation_score = escalation.escalation_score
        case.urgency = escalation.urgency

        # Step 4: Legal knowledge retrieval
        retriever = LegalKnowledgeRetriever()
        case.legal_rights = await retriever.retrieve(case)
        await retriever.close()

        # Step 5: Courtroom simulation
        swarm = CourtroomSwarm(n_agents_per_type=100)
        sim = swarm.simulate(case, mock=True)
        case.simulation_result = {
            "win_probability": sim.overall_win_probability,
            "strategy": sim.recommended_strategy,
        }

        # Step 6: Document generation
        generator = LegalDocumentGenerator()
        case.recommended_actions = generator.build_action_plan(case)
        case.generated_documents = generator.generate_all_documents(case)

        # Step 7: Human alert if critical
        if escalation.requires_human:
            alerter = VolunteerAlerter()
            await alerter.alert(case, escalation)
            case.human_volunteer_alerted = True

        # Store for retrieval
        _case_store[case.case_id] = case

        # Build response
        return CaseResponse(
            case_id=case.case_id,
            case_type=case.case_type.value,
            urgency=case.urgency.name,
            country=case.country,
            language=case.language,
            escalation_score=case.escalation_score,
            requires_human_lawyer=escalation.requires_human,
            human_volunteer_alerted=case.human_volunteer_alerted,
            analyzed_at=datetime.now(timezone.utc),
            legal_rights=[
                LegalRightResponse(
                    right=r.right, statute=r.statute,
                    jurisdiction=r.jurisdiction,
                    plain_english=r.plain_english,
                    source_url=r.source_url or "",
                ) for r in case.legal_rights[:5]
            ],
            recommended_actions=[
                ActionResponse(
                    step_number=a.step_number, action=a.action,
                    deadline=a.deadline, how_to=a.how_to,
                    requires_human=a.requires_human,
                ) for a in case.recommended_actions
            ],
            simulation=SimulationResponse(
                win_probability=sim.overall_win_probability,
                recommended_strategy=sim.recommended_strategy,
                best_argument=sim.key_arguments[0].argument if sim.key_arguments else "",
                judge_concerns=sim.judge_likely_concerns[:3],
                what_to_avoid=sim.what_to_avoid[:2],
                best_opening_statement=sim.best_opening_statement,
            ),
            documents=[
                DocumentResponse(
                    doc_type=d.doc_type, title=d.title,
                    content=d.content, citations=d.citations,
                    generated_at=d.generated_at,
                ) for d in case.generated_documents
            ],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/{case_id}", response_model=CaseResponse, tags=["Cases"])
async def get_case(case_id: str):
    """Retrieve a previously analyzed case."""
    case = _case_store.get(case_id.upper())
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    return CaseResponse(
        case_id=case.case_id, case_type=case.case_type.value,
        urgency=case.urgency.name, country=case.country,
        language=case.language, escalation_score=case.escalation_score,
        requires_human_lawyer=case.human_volunteer_alerted,
        human_volunteer_alerted=case.human_volunteer_alerted,
        analyzed_at=datetime.now(timezone.utc),
        legal_rights=[], recommended_actions=[], documents=[],
    )
