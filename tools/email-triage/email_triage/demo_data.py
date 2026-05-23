"""A sample inbox so the tool runs with zero credentials via `--demo`."""

from __future__ import annotations

SAMPLE_EMAILS: list[dict[str, str]] = [
    {
        "id": "demo-1",
        "sender": "Dr. Patel's Office <appointments@clinic.example>",
        "subject": "Appointment reminder: tomorrow 9:00 AM",
        "snippet": "This is a reminder of your appointment tomorrow at 9:00 AM. "
        "Reply CONFIRM or call to reschedule.",
        "date": "Mon, 23 May 2026 07:40:00",
    },
    {
        "id": "demo-2",
        "sender": "Jordan Lee <jordan@workmail.example>",
        "subject": "Can you review the deck before the 3pm call?",
        "snippet": "Hey — could you take a look at slides 4-6 and send comments "
        "before our 3pm sync today? Thanks!",
        "date": "Mon, 23 May 2026 08:05:00",
    },
    {
        "id": "demo-3",
        "sender": "The Morning Brew <crew@morningbrew.example>",
        "subject": "☕ Markets wobble, a new AI gadget, and more",
        "snippet": "Good morning. Here's everything you need to know to start "
        "your day in 5 minutes...",
        "date": "Mon, 23 May 2026 06:00:00",
    },
    {
        "id": "demo-4",
        "sender": "ShoeStore <deals@shoestore.example>",
        "subject": "🔥 48 hours only: 40% off everything",
        "snippet": "Our biggest sale of the season ends soon. Use code SAVE40 at "
        "checkout. Shop now before it's gone!",
        "date": "Sun, 22 May 2026 19:30:00",
    },
    {
        "id": "demo-5",
        "sender": "Amazon <auto-confirm@amazon.example>",
        "subject": "Your order has shipped (#114-2920)",
        "snippet": "Your package is on the way and should arrive Tuesday. Track "
        "your shipment for the latest updates.",
        "date": "Sun, 22 May 2026 21:10:00",
    },
    {
        "id": "demo-6",
        "sender": "LinkedIn <notifications@linkedin.example>",
        "subject": "Sam and 3 others viewed your profile",
        "snippet": "See who's been checking out your profile this week and grow "
        "your network.",
        "date": "Sun, 22 May 2026 12:00:00",
    },
    {
        "id": "demo-7",
        "sender": "Billing <billing@cloudhost.example>",
        "subject": "Action required: payment failed for invoice #8841",
        "snippet": "We couldn't process your payment. Please update your card by "
        "May 25 to avoid service interruption.",
        "date": "Mon, 23 May 2026 05:15:00",
    },
    {
        "id": "demo-8",
        "sender": "Growth Partners <outreach@coldleads.example>",
        "subject": "Quick question about your sales pipeline",
        "snippet": "I help companies like yours 10x revenue. Do you have 15 minutes "
        "this week for a quick call? Just reply YES.",
        "date": "Sat, 21 May 2026 14:22:00",
    },
    {
        "id": "demo-9",
        "sender": "School Office <office@school.example>",
        "subject": "Field trip permission slip due Friday",
        "snippet": "Please sign and return the attached permission slip for the "
        "museum trip by this Friday.",
        "date": "Fri, 20 May 2026 16:00:00",
    },
    {
        "id": "demo-10",
        "sender": "GitHub <noreply@github.example>",
        "subject": "[repo] Your CI run passed",
        "snippet": "All checks have passed on your latest commit to main. No action "
        "needed.",
        "date": "Mon, 23 May 2026 02:45:00",
    },
]
