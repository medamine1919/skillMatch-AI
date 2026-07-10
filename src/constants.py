from __future__ import annotations

SPECIALITIES = [
    "AI/Data",
    "Web Dev",
    "Robotics/Embedded",
    "Mobile",
    "Cybersecurity",
    "Programming for Kids",
]

DECISION_LABELS = {
    "excellent": "Excellent Fit",
    "strong": "Strong Fit",
    "moderate": "Moderate Fit",
    "weak": "Weak Fit",
}

RECOMMENDATION_LABELS = {
    "recommended": "Recommended",
    "review": "Review Manually",
    "not_recommended": "Not Recommended",
}

SUPPORTED_INPUT_MODES = [
    "free_need",
    "job_offer",
]

CHILD_FRIENDLY_SOFT_SKILLS = [
    "empathy",
    "communication",
    "patience",
    "pedagogy",
    "kindness",
    "teamwork",
    "responsibility",
    "adaptability",
    "creativity",
    "mentoring",
]

TECH_SPECIALITY_HINTS = {
    "AI/Data": [
        "python", "machine learning", "deep learning", "nlp", "sql",
        "power bi", "data analysis", "pandas", "numpy", "scikit-learn", "ai"
    ],
    "Web Dev": [
        "html", "css", "javascript", "typescript", "angular",
        "react", "spring boot", "node.js", "java", "web", "frontend", "backend"
    ],
    "Robotics/Embedded": [
        "arduino", "raspberry pi", "embedded", "c", "c++",
        "robotics", "sensors", "microcontroller", "ros", "electronics"
    ],
    "Mobile": [
        "flutter", "android", "ios", "kotlin", "swift", "react native", "mobile"
    ],
    "Cybersecurity": [
        "security", "cybersecurity", "pentest", "network security",
        "owasp", "soc", "siem", "firewall"
    ],
    "Programming for Kids": [
        "scratch", "blockly", "kids coding", "teaching", "tutoring",
        "workshop", "children", "teenagers", "education", "pedagogy"
    ],
}
