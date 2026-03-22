#!/usr/bin/env python3
# scripts/run_demo.py — Interactive demo with menu
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from dotenv import load_dotenv
load_dotenv()

DEMO_CASES = {
    "1": ("Karachi housing lockout (English)",
          "My landlord changed the locks tonight and threw my belongings outside in Karachi, Pakistan. I have three children and nowhere to sleep."),
    "2": ("Urdu housing case",
          "میرے مالک مکان نے آج رات تالہ بدل دیا اور میرا سامان باہر پھینک دیا۔ کراچی میں ہوں۔"),
    "3": ("US labor - unpaid wages",
          "My employer in New York has not paid my salary for 2 months. They are threatening to fire me if I complain."),
    "4": ("UK wrongful eviction",
          "My landlord in London gave me only 3 days notice to leave. My tenancy is an assured shorthold tenancy."),
    "5": ("Indonesia labor dispute",
          "Majikan saya tidak membayar gaji saya selama 3 bulan dan mengancam akan memecat saya di Jakarta."),
    "6": ("Criminal arrest rights",
          "Police arrested me without showing any warrant. They have not told me what I am charged with. I am being held at the station."),
    "7": ("Custom case - type your own", None),
}

async def main():
    print("\n" + "="*55)
    print("LEXSWARM — AI Legal Defense System")
    print("5 billion people. Zero lawyers. One solution.")
    print("="*55)
    print("\nSelect a demo case:")
    for k, (label, _) in DEMO_CASES.items():
        print(f"  [{k}] {label}")
    print()
    choice = input("Enter number (1-7): ").strip()

    label, description = DEMO_CASES.get(choice, ("Unknown", None))
    if description is None:
        description = input("\nDescribe your legal situation: ").strip()

    print(f"\nRunning: {label}")
    print(f"Input: {description[:100]}...\n")

    from scripts.run_lexswarm import run_case
    await run_case(description)

if __name__ == "__main__":
    asyncio.run(main())
