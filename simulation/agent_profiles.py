# simulation/agent_profiles.py
# Detailed agent profiles for courtroom simulation
# Each agent type has personality traits, biases, and decision patterns

from dataclasses import dataclass


@dataclass
class AgentProfile:
    agent_type: str
    description: str
    primary_focus: list[str]
    receptive_to: list[str]
    skeptical_of: list[str]
    key_questions: list[str]
    decision_weight: float   # weight in final outcome probability


AGENT_PROFILES = {

    "judge": AgentProfile(
        agent_type="judge",
        description="Impartial arbitrator of law. Values precedent, procedure, and statutory compliance.",
        primary_focus=["legal precedent", "procedural correctness", "statutory interpretation", "burden of proof"],
        receptive_to=["direct statute citations", "documented evidence", "case law precedent",
                      "procedural compliance", "clear legal argument"],
        skeptical_of=["emotional arguments without legal basis", "hearsay evidence",
                      "unsupported factual claims", "vague assertions"],
        key_questions=[
            "What specific statute supports this argument?",
            "Has the correct legal procedure been followed?",
            "What precedent exists for this position?",
            "Has the burden of proof been met?",
            "Is this evidence admissible?",
        ],
        decision_weight=0.40,
    ),

    "jury": AgentProfile(
        agent_type="jury",
        description="Lay people assessing facts. Respond to clear narrative, credibility, and common sense.",
        primary_focus=["common sense", "credibility of witnesses", "emotional resonance", "fairness"],
        receptive_to=["clear simple narrative", "relatable circumstances", "physical evidence",
                      "consistent testimony", "sympathetic presentation"],
        skeptical_of=["complex legal jargon", "contradictory testimony",
                      "unsympathetic presentation", "overly technical arguments"],
        key_questions=[
            "Does this person seem credible?",
            "Does the story make sense?",
            "Is this outcome fair?",
            "What would a reasonable person do?",
        ],
        decision_weight=0.25,
    ),

    "prosecution": AgentProfile(
        agent_type="prosecution",
        description="Adversarial agent arguing against the applicant. Seeks to weaken your case.",
        primary_focus=["weaknesses in evidence", "prior conduct", "procedural violations",
                       "burden not met", "credibility attacks"],
        receptive_to=["prior offences", "inconsistencies in testimony", "missing documentation",
                      "procedural errors by applicant"],
        skeptical_of=["your strongest points — will always challenge"],
        key_questions=[
            "Can the applicant prove this claim with documentation?",
            "Is there evidence of prior violations by the applicant?",
            "Has the applicant followed required procedures?",
            "Are there inconsistencies in the narrative?",
        ],
        decision_weight=0.10,
    ),

    "defense": AgentProfile(
        agent_type="defense",
        description="Advocate for the applicant. Identifies strongest legal arguments.",
        primary_focus=["rights violations", "reasonable doubt", "mitigating factors",
                       "procedural errors by respondent"],
        receptive_to=["documented rights violations", "evidence of bad faith by respondent",
                      "procedural failures", "character references", "alibi evidence"],
        skeptical_of=["weak emotional arguments without legal backing"],
        key_questions=[
            "What is the strongest statutory argument?",
            "Were the applicant's rights violated?",
            "Is there documented evidence?",
            "What mitigating factors apply?",
        ],
        decision_weight=0.15,
    ),

    "opposing_counsel": AgentProfile(
        agent_type="opposing_counsel",
        description="Lawyer for the other side. Professionally adversarial.",
        primary_focus=["client's interests", "applicant's legal weaknesses",
                       "settlement leverage", "technical defences"],
        receptive_to=["any weakness in your case", "missing documentation",
                      "missed deadlines", "procedural errors"],
        skeptical_of=["your strongest arguments — actively preparing counter-arguments"],
        key_questions=[
            "What documentation does the applicant actually have?",
            "Have any deadlines been missed?",
            "Are there technical defences available?",
            "Is settlement in the client's interest?",
        ],
        decision_weight=0.10,
    ),
}


def get_profile(agent_type: str) -> AgentProfile:
    return AGENT_PROFILES.get(agent_type, AGENT_PROFILES["judge"])


def get_all_profiles() -> dict[str, AgentProfile]:
    return AGENT_PROFILES
