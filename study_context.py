from __future__ import annotations

GROUP_INFO = {
    "1A": {
        "condition": "Personalized daily",
        "course_order": "Creative Thinking → Introduction to ML",
        "reminder_label": "Personalized daily",
    },
    "1B": {
        "condition": "Personalized daily",
        "course_order": "Introduction to ML → Creative Thinking",
        "reminder_label": "Personalized daily",
    },
    "2A": {
        "condition": "Weekly reminder",
        "course_order": "Creative Thinking → Introduction to ML",
        "reminder_label": "Weekly reminder",
    },
    "2B": {
        "condition": "Weekly reminder",
        "course_order": "Introduction to ML → Creative Thinking",
        "reminder_label": "Weekly reminder",
    },
}

DEFAULT_RQ_SUMMARY = [
    {
        "RQ Code": "RQ2a-1",
        "Lens": "Completion",
        "Research Question": "Nudging Effect on Completion: To what extent does personalized daily nudging increase module completion rates compared to weekly reminder-only nudging among working adult learners?",
        "Main Themes": [
            "Reminder pressure could sustain completion while undermining control",
            "Action depended on opportunity and schedule",
            "Completion is distinct from meaningful engagement",
        ],
        "Preliminary Synthesis": "Perceived completion benefits were mixed and not established as a direct causal effect. Participants described reminders as useful for remembering and as intrusive when they repeated after completion or disrupted routines.",
    },
    {
        "RQ Code": "RQ2a-2",
        "Lens": "Habit formation",
        "Research Question": "Habit Formation: How do personalized daily nudges and weekly generic reminders shape self-reported habit strength, routine dependence and autonomous re-engagement?",
        "Main Themes": [
            "Deliberate scheduling rather than automatic habit",
            "Intermittent self-initiated use",
            "Reminder dependence and routine substitution",
        ],
        "Preliminary Synthesis": "Several accounts described deliberate scheduling or existing routines more than independent habit formation. The interviews suggest reminder-supported remembering rather than a stable autonomous habit.",
    },
    {
        "RQ Code": "RQ2a-3",
        "Lens": "Routine integration",
        "Research Question": "Routine Integration: When and how do participants integrate the intervention into daily or weekly routines, and which barriers interfere with participation?",
        "Main Themes": [
            "Commute and short work-break windows",
            "Weekend and home-based variation",
            "Competing work, family and topic demands",
        ],
        "Preliminary Synthesis": "Short sessions fit naturally into commute and break windows, but the system was disrupted by unpredictable work, family demands and topic relevance. Routine fit therefore depended on both time and context.",
    },
    {
        "RQ Code": "RQ2a-4",
        "Lens": "Intrusiveness",
        "Research Question": "Perceived Intrusiveness: How do participants experience reminder timing and frequency, and how is intrusiveness related to perceived helpfulness and routine fit?",
        "Main Themes": [
            "Dose and timing problems",
            "Perceived pressure after completion",
            "Circumstantial tolerance versus aversion",
        ],
        "Preliminary Synthesis": "Intrusiveness varied with dose, persistence after completion and perceived usefulness. Several participants tolerated reminders when they were brief and actionable, while others described them as pressure, distraction or unwanted intrusions.",
    },
]

DEFAULT_CODES = [
    {"code_id": "C01", "name": "Reminder prevents forgetting", "category": "Reminders and action", "definition": "Participant attributes remembering or re-engagement to reminders.", "include": "Include participant attribution of remembering or continuation to reminders.", "exclude": "Exclude mere receipt of a notification without interpretation.", "rq_codes": ["RQ2a-1", "RQ2a-2"]},
    {"code_id": "C02", "name": "Action deferred during competing tasks", "category": "Routine fit", "definition": "Participant delays app use because of competing work, family or practical constraints.", "include": "Include immediate deferral or scheduling delay linked to competing demands.", "exclude": "Exclude general work stress with no direct link to action.", "rq_codes": ["RQ2a-3"]},
    {"code_id": "C03", "name": "Frequent prompts or persistence after completion", "category": "Pressure and delivery fidelity", "definition": "Participant reports repeated alerts, dose issues, or reminders after the task was already done.", "include": "Include repeated alerts, high perceived dose, and reminders after completion.", "exclude": "Do not infer confirmed technical fault from a participant account alone.", "rq_codes": ["RQ2a-1", "RQ2a-4"]},
    {"code_id": "C04", "name": "Completion to silence notifications", "category": "Pressure and delivery fidelity", "definition": "Participant completes or opens the app to stop the reminder rather than because of sustained interest.", "include": "Include completing or opening to stop alerts or anticipated irritation.", "exclude": "Exclude completion motivated by genuine learning interest alone.", "rq_codes": ["RQ2a-1", "RQ2a-4"]},
    {"code_id": "C05", "name": "Contextual timing fit", "category": "Routine integration", "definition": "Participant describes commute, work breaks or before-bed contexts as enabling engagement.", "include": "Include time-window fit to context, routine and schedule.", "exclude": "Exclude generic statements without a time context.", "rq_codes": ["RQ2a-3"]},
    {"code_id": "C06", "name": "Topic relevance and learning value", "category": "Motivation and quality", "definition": "Participant links engagement to topic interest, relevance or perceived learning value.", "include": "Include comments about relevance, interest, challenge or quality.", "exclude": "Exclude optics, interface style alone if no relevance judgement appears.", "rq_codes": ["RQ2a-1", "RQ2a-2", "RQ2a-3"]},
]

PRELIMINARY_THEMES = [
    {
        "theme": "Reminder pressure could sustain completion while undermining control",
        "subtheme": "Frequent prompts or persistence after completion",
        "category": "Pressure and delivery fidelity",
        "status": "Provisional",
    },
    {
        "theme": "Short sessions fit routines, but flexibility limits remained",
        "subtheme": "Commute, work breaks and before-work windows",
        "category": "Routine integration",
        "status": "Provisional",
    },
    {
        "theme": "Topic relevance and content quality shaped engagement more than reminder volume alone",
        "subtheme": "Motivation and meaningful learning",
        "category": "Learning value",
        "status": "Provisional",
    },
    {
        "theme": "Deliberate scheduling and existing routines were more common than autonomous habit",
        "subtheme": "Reminder dependence versus habit",
        "category": "Habit formation",
        "status": "Provisional",
    },
    {
        "theme": "Useful personalization required choice, transparency and timing control",
        "subtheme": "Design preferences and privacy boundaries",
        "category": "Personalization",
        "status": "Provisional",
    },
    {
        "theme": "Exposure and delivery faults must be separated from intended reminder design",
        "subtheme": "Experienced accounts versus technical issues",
        "category": "Evidence quality",
        "status": "Provisional",
    },
]

METHOD_TEXT = "Framework Method with RQ-led organizing domains and inductive codes developed from participant accounts. Excerpt selection and comparison were iterative and subject to human review."

REVIEW_STATUSES = ["Pending", "Approved", "Needs Revision", "Rejected"]
EVIDENCE_TYPES = ["Direct quote", "Experienced account", "Hypothetical preference", "Qualified position", "Unclear attribution"]
