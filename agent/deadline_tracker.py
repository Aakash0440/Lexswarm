# agent/deadline_tracker.py
# Tracks legal deadlines and sends Telegram reminders
# Legal deadlines are often case-critical — missing them loses your rights permanently

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from intake.base import UrgencyLevel, CaseType


@dataclass
class LegalDeadline:
    case_id: str
    description: str
    due_at: datetime
    consequence: str         # what happens if you miss this
    action_required: str     # exactly what to do before deadline
    reminder_sent: bool = False
    completed: bool = False


DEADLINE_TEMPLATES = {
    CaseType.HOUSING: [
        {"hours": 24,    "desc": "Send demand letter to landlord",
         "consequence": "Delay weakens your legal position"},
        {"hours": 48,    "desc": "File complaint with housing authority if no response",
         "consequence": "You may lose right to emergency housing relief"},
        {"hours": 168,   "desc": "File court application if situation not resolved",
         "consequence": "Illegal eviction may be treated as abandoned if not challenged"},
    ],
    CaseType.LABOR: [
        {"hours": 72,    "desc": "File complaint with Labour Department",
         "consequence": "Wage theft claims have limitation periods — delay risks losing claim"},
        {"hours": 720,   "desc": "File formal labor claim in court (30 days)",
         "consequence": "Many jurisdictions have 30-day limitation for wrongful termination"},
    ],
    CaseType.CRIMINAL: [
        {"hours": 24,    "desc": "Apply for bail if detained",
         "consequence": "Extended detention without bail hearing is unlawful"},
        {"hours": 48,    "desc": "File motion to suppress illegally obtained evidence",
         "consequence": "Evidence suppression rights may be waived if not raised promptly"},
    ],
    CaseType.IMMIGRATION: [
        {"hours": 24,    "desc": "File stay of removal if deportation ordered",
         "consequence": "Deportation cannot be reversed once executed"},
        {"hours": 168,   "desc": "File asylum application within required window",
         "consequence": "Asylum applications have strict time limits in most jurisdictions"},
    ],
}


class DeadlineTracker:
    """Tracks filing deadlines and sends Telegram reminders."""

    def __init__(self):
        self.deadlines: list[LegalDeadline] = []

    def set_deadlines(self, case) -> list[LegalDeadline]:
        """Set appropriate deadlines based on case type and urgency."""
        now = datetime.now(timezone.utc)
        templates = DEADLINE_TEMPLATES.get(case.case_type, [])

        # Compress deadlines for critical urgency
        urgency_multiplier = {
            UrgencyLevel.CRITICAL: 0.25,
            UrgencyLevel.HIGH:     0.5,
            UrgencyLevel.MEDIUM:   1.0,
            UrgencyLevel.LOW:      2.0,
        }.get(case.urgency, 1.0)

        new_deadlines = []
        for tmpl in templates:
            adjusted_hours = tmpl["hours"] * urgency_multiplier
            deadline = LegalDeadline(
                case_id=case.case_id,
                description=tmpl["desc"],
                due_at=now + timedelta(hours=adjusted_hours),
                consequence=tmpl["consequence"],
                action_required=tmpl["desc"],
            )
            new_deadlines.append(deadline)
            self.deadlines.append(deadline)

        return new_deadlines

    async def send_reminder(self, deadline: LegalDeadline, alerter) -> None:
        """Send Telegram reminder for an approaching deadline."""
        hours_left = (deadline.due_at - datetime.now(timezone.utc)).total_seconds() / 3600
        msg = (
            f"LEXSWARM DEADLINE REMINDER\n\n"
            f"Case: {deadline.case_id}\n"
            f"Action: {deadline.description}\n"
            f"Due: {deadline.due_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"Time left: {hours_left:.1f} hours\n\n"
            f"If you miss this: {deadline.consequence}\n\n"
            f"What to do: {deadline.action_required}"
        )
        await alerter.send(msg)
        deadline.reminder_sent = True

    def get_upcoming(self, hours: float = 24.0) -> list[LegalDeadline]:
        """Get deadlines due within the next N hours."""
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(hours=hours)
        return [
            d for d in self.deadlines
            if not d.completed and not d.reminder_sent
            and now < d.due_at <= cutoff
        ]

    def mark_complete(self, case_id: str, description: str) -> None:
        for d in self.deadlines:
            if d.case_id == case_id and d.description == description:
                d.completed = True
                break
