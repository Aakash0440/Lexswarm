# alerts/volunteer_alert.py
# Alerts human volunteer lawyers when a case is CRITICAL
# Uses Telegram (same stack as QUANTSHIFT) + console fallback

import os


class VolunteerAlerter:
    def __init__(self):
        self.token   = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("VOLUNTEER_CHAT_ID", os.getenv("TELEGRAM_CHAT_ID"))

    async def alert(self, case, escalation) -> None:
        msg = (
            f"LEXSWARM — URGENT CASE ALERT\n\n"
            f"Case ID:  {case.case_id}\n"
            f"Type:     {case.case_type.value}\n"
            f"Country:  {case.country}\n"
            f"Urgency:  {case.urgency.name}\n"
            f"Score:    {escalation.escalation_score:.0%}\n"
            f"Respond:  within {escalation.recommended_response_hours}h\n\n"
            f"Triggers: {', '.join(escalation.triggers[:3])}\n\n"
            f"Summary:  {case.raw_description[:200]}\n\n"
            f"ACTION REQUIRED: Review and contact person immediately."
        )

        if self.token and self.chat_id:
            try:
                from telegram import Bot
                bot = Bot(token=self.token)
                await bot.send_message(chat_id=self.chat_id, text=msg)
                print(f"[VolunteerAlert] Telegram alert sent for case {case.case_id}")
            except Exception as e:
                print(f"[VolunteerAlert] Telegram failed: {e}")
                print(f"[VolunteerAlert] ALERT:\n{msg}")
        else:
            print(f"[VolunteerAlert] ALERT:\n{msg}")
