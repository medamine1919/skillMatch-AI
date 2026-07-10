from __future__ import annotations

from pathlib import Path

import pandas as pd


def export_result_to_csv(export_path: str | Path, cv_data: dict, req_data: dict, result: dict) -> Path:
    export_path = Path(export_path)
    rows = [
        {"field": "candidate_name", "value": cv_data.get("full_name", "")},
        {"field": "email", "value": cv_data.get("email", "")},
        {"field": "phone", "value": cv_data.get("phone", "")},
        {"field": "cv_speciality", "value": result.get("cv_speciality", "")},
        {"field": "requirement_speciality", "value": result.get("requirement_speciality", "")},
        {"field": "final_score", "value": result.get("final_score", 0)},
        {"field": "decision_label", "value": result.get("decision_label", "")},
        {"field": "recommendation_label", "value": result.get("recommendation_label", "")},
        {"field": "matched_required_skills", "value": ", ".join(result.get("skill_result", {}).get("matched_required", []))},
        {"field": "missing_required_skills", "value": ", ".join(result.get("skill_result", {}).get("missing_required", []))},
        {"field": "short_explanation", "value": result.get("short_explanation", "")},
        {"field": "detailed_explanation", "value": result.get("detailed_explanation", "")},
    ]
    df = pd.DataFrame(rows)
    export_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(export_path, index=False, encoding="utf-8-sig")
    return export_path
