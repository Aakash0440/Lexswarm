# agent/action_planner.py
# Generates rich, jurisdiction-aware action plans
# Goes beyond the basic document generator — includes contact info,
# phone numbers, websites, and step-by-step filing instructions

from intake.base import CaseType, UrgencyLevel, LegalCase, RecommendedAction


# ── Jurisdiction-specific resources ───────────────────────────────────────────

LEGAL_AID_RESOURCES = {
    "PK": {
        "general":    "Pakistan Bar Council — pbcpakistan.org",
        "housing":    "Karachi: Sindh High Court Legal Aid Committee — 021-9921-2571",
        "labor":      "National Industrial Relations Commission — nirc.gov.pk",
        "criminal":   "Legal Aid Society Pakistan — legalaidsociety.com.pk",
        "emergency":  "Edhi Foundation legal aid — 115",
    },
    "US": {
        "general":    "LawHelp.org — lawhelp.org",
        "housing":    "National Housing Law Project — nhlp.org",
        "labor":      "US Department of Labor Wage Hour Division — 1-866-487-9243",
        "criminal":   "Public Defender Office (ask police or court)",
        "immigration":"RAICES — raicestexas.org | CLINIC — cliniclegal.org",
        "emergency":  "LawHelp Interactive — lawhelpinteractive.org",
    },
    "GB": {
        "general":    "Citizens Advice — citizensadvice.org.uk | 0800 144 8848",
        "housing":    "Shelter — shelter.org.uk | 0808 800 4444",
        "labor":      "ACAS — acas.org.uk | 0300 123 1100",
        "criminal":   "Legal Aid (gov.uk/legal-aid)",
        "immigration":"Migrants' Rights Network — migrantsrights.org.uk",
        "emergency":  "Law Society Solicitor Finder — solicitors.lawsociety.org.uk",
    },
    "IN": {
        "general":    "National Legal Services Authority — nalsa.gov.in | 15100",
        "labor":      "Labour Commissioner Office (state-specific)",
        "housing":    "District Collector office for housing complaints",
        "criminal":   "State Legal Services Authority (SLSA) — free representation",
        "emergency":  "NALSA helpline — 15100 (toll free)",
    },
    "ID": {
        "general":    "YLBHI (Yayasan Lembaga Bantuan Hukum Indonesia) — ylbhi.or.id",
        "labor":      "Dinas Tenaga Kerja (Disnaker) — local office",
        "housing":    "Komnas HAM — komnasham.go.id",
        "criminal":   "Lembaga Bantuan Hukum (LBH) — free legal aid",
        "emergency":  "Hotline pengaduan: 1500-518",
    },
    "XX": {
        "general":    "UN Human Rights — ohchr.org/en/get-involved/individual-complaints",
        "emergency":  "International Legal Foundation — theilf.org",
    }
}

# ── Action templates by case type and urgency ──────────────────────────────────

ACTIONS_CRITICAL = {
    CaseType.HOUSING: [
        ("Call emergency legal aid", "within 30 minutes",
         "Search '[your city] emergency housing legal aid' or use the resource below. Explain you have been illegally locked out tonight."),
        ("Document the lockout immediately", "now",
         "Take photos/video of the changed locks, your belongings outside, any notes from the landlord. Timestamp everything."),
        ("Send demand letter via WhatsApp/email tonight", "within 2 hours",
         "Use the generated demand letter. Send via WhatsApp message AND email to your landlord. Screenshot the delivery."),
        ("Contact police if landlord refuses access", "if no response in 1 hour",
         "Illegal lockout is a criminal offence in most jurisdictions. Show police the demand letter and your tenancy agreement."),
        ("File emergency court application tomorrow morning", "by 9am tomorrow",
         "Court emergency housing applications are usually heard same day. Bring: tenancy agreement, demand letter, landlord's non-response evidence."),
    ],
    CaseType.CRIMINAL: [
        ("Assert your right to remain silent immediately", "NOW",
         "Say clearly: 'I am exercising my right to remain silent. I want a lawyer.' Say nothing else until a lawyer is present."),
        ("Request a lawyer or public defender", "NOW",
         "Say: 'I want a lawyer.' If you cannot afford one, say: 'I cannot afford a lawyer. I request a public defender.' Do not answer questions until lawyer arrives."),
        ("Note all officer details", "as soon as possible",
         "Remember or write: officer names, badge numbers, time of arrest, location, what was said. This is critical for any later complaint or defence."),
        ("Contact family or trusted person", "within 1 hour",
         "You have the right to inform someone of your arrest. Give them: your location, what you are charged with, the lawyer's name if known."),
    ],
    CaseType.IMMIGRATION: [
        ("Do not sign anything without a lawyer", "immediately",
         "Immigration authorities may ask you to sign a 'voluntary departure' form. Signing waives your right to a hearing. DO NOT sign."),
        ("Request a deportation hearing", "NOW",
         "Say clearly: 'I am requesting a hearing before an immigration judge. I do not agree to voluntary departure.'"),
        ("Contact an immigration legal aid organization", "within 1 hour",
         "Use the legal aid resource below. Explain you have a deportation order and need emergency representation."),
        ("Gather all documents immediately", "now",
         "Collect: passport, visa, entry stamps, any proof of residence/work/family ties, receipts showing time in country."),
    ],
}

ACTIONS_HIGH = {
    CaseType.LABOR: [
        ("Document all wage evidence", "today",
         "Collect: pay stubs, bank statements, employment contract, any written communications about wages. Screenshot everything."),
        ("Send formal demand letter", "within 24 hours",
         "Use the generated demand letter. Send by registered post AND email. Keep proof of delivery."),
        ("File complaint with labour department", "within 48 hours if no response",
         "Use the legal aid resource below to find your local labour department. Bring copies of all documents."),
        ("File court claim if wages unpaid after 7 days", "within 7 days",
         "Small claims court handles wage disputes in most jurisdictions. Filing fee is usually waived for low-income claimants."),
    ],
    CaseType.FAMILY: [
        ("File for emergency protective order if domestic violence", "within 24 hours",
         "Courts issue emergency protective orders same-day in domestic violence cases. Go to the courthouse directly."),
        ("Document all incidents with dates and details", "immediately",
         "Keep a log: date, time, what happened, any witnesses, any injuries. Photos of injuries are important evidence."),
        ("Contact domestic violence support service", "today",
         "National helplines are available in all countries — they provide safe housing, legal advice, and support."),
    ],
}

ACTIONS_STANDARD = [
    ("Send formal demand letter", "within 3 days",
     "Use the generated demand letter. Fill in the [BRACKETED] fields. Send by registered post. Keep proof of delivery."),
    ("Document all evidence", "as soon as possible",
     "Collect all relevant documents, messages, photos, receipts. Create a timeline of events with dates."),
    ("File official complaint if no response", "within 7 days of sending demand letter",
     "Use the contact below to file with the relevant government authority."),
    ("Consult a legal aid lawyer", "within 2 weeks",
     "For free legal advice, contact the resource listed below. Many offer free 30-minute consultations."),
]


class ActionPlanner:
    """
    Generates rich, jurisdiction-aware action plans.
    Each action includes: what to do, when to do it, how to do it, contacts.
    """

    def get_legal_resource(self, country: str, case_type: CaseType) -> str:
        """Get jurisdiction-specific legal aid resource."""
        resources = LEGAL_AID_RESOURCES.get(country, LEGAL_AID_RESOURCES["XX"])
        return resources.get(case_type.value, resources.get("general", "Contact your local legal aid office"))

    def build_plan(self, case: LegalCase) -> list[RecommendedAction]:
        """Build complete action plan based on case type and urgency."""
        actions = []
        step = 1

        # Get urgency-specific actions
        if case.urgency == UrgencyLevel.CRITICAL:
            type_actions = ACTIONS_CRITICAL.get(case.case_type, [])
            for action_text, deadline, how_to in type_actions:
                actions.append(RecommendedAction(
                    step_number=step, action=action_text,
                    deadline=deadline, how_to=how_to,
                    urgency=UrgencyLevel.CRITICAL,
                    requires_human=(step == 1),
                ))
                step += 1

        elif case.urgency == UrgencyLevel.HIGH:
            type_actions = ACTIONS_HIGH.get(case.case_type, [])
            for action_text, deadline, how_to in type_actions:
                actions.append(RecommendedAction(
                    step_number=step, action=action_text,
                    deadline=deadline, how_to=how_to,
                    urgency=UrgencyLevel.HIGH,
                    requires_human=False,
                ))
                step += 1

        # Always add standard actions if we don't have enough
        if len(actions) < 3:
            for action_text, deadline, how_to in ACTIONS_STANDARD:
                actions.append(RecommendedAction(
                    step_number=step, action=action_text,
                    deadline=deadline, how_to=how_to,
                    urgency=case.urgency,
                    requires_human=False,
                ))
                step += 1

        # Always add legal aid resource as final step
        resource = self.get_legal_resource(case.country, case.case_type)
        actions.append(RecommendedAction(
            step_number=step,
            action="Contact free legal aid in your area",
            deadline="as soon as possible",
            how_to=resource,
            urgency=case.urgency,
            requires_human=True,
        ))

        return actions
