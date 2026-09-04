# -*- coding: utf-8 -*-
"""
Export script to write the complete multilingual machine instruction manual
into separate .txt files in data/manuals/.
"""

import os
import sys

# Ensure repository root is in sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.multilingual_manual_data import MULTILINGUAL_MANUAL


def manual_to_formatted_text(data):
    lines = []
    lines.append("=" * 80)
    lines.append(f"{data['machine_name']} — [{data['language_label']}]")
    lines.append("=" * 80)
    lines.append("")

    s = data["sections"]

    # 1. Overview
    lines.append("-" * 80)
    lines.append(s["overview"]["title"])
    lines.append("-" * 80)
    lines.append(f"Machine Name: {s['overview']['machine_name']}")
    lines.append(f"Purpose: {s['overview']['machine_purpose']}")
    lines.append("Main Components:")
    for c in s["overview"]["main_components"]:
        lines.append(f"  * {c}")
    lines.append(f"Operating Principle: {s['overview']['basic_operating_principle']}")
    lines.append("")

    # 2. Safety
    lines.append("-" * 80)
    lines.append(s["safety"]["title"])
    lines.append("-" * 80)
    lines.append("[Safety Precautions]")
    for sp in s["safety"]["safety_precautions"]:
        lines.append(f"  * {sp}")
    lines.append("\n[Electrical Safety]")
    for es in s["safety"]["electrical_safety"]:
        lines.append(f"  * {es}")
    lines.append("\n[Emergency Procedures]")
    for ep in s["safety"]["emergency_procedures"]:
        lines.append(f"  * {ep}")
    lines.append("\n[Warnings]")
    for w in s["safety"]["warnings"]:
        lines.append(f"  ! {w}")
    lines.append("\n[Required Protective Equipment (PPE)]")
    for ppe in s["safety"]["required_protective_equipment"]:
        lines.append(f"  + {ppe}")
    lines.append("")

    # 3. Components
    lines.append("-" * 80)
    lines.append(s["components"]["title"])
    lines.append("-" * 80)
    for c in s["components"]["components_list"]:
        lines.append(f"Component: {c['name']}")
        lines.append(f"  Function:           {c['function']}")
        lines.append(f"  Normal Condition:   {c['normal_condition']}")
        lines.append(f"  Common Problems:    {c['common_problems']}")
        lines.append("")

    # 4. Operating Instructions
    lines.append("-" * 80)
    lines.append(s["operating"]["title"])
    lines.append("-" * 80)
    for cat, steps in s["operating"]["steps"].items():
        cat_title = cat.replace("_", " ").title()
        lines.append(f"[{cat_title}]")
        for idx, step in enumerate(steps, 1):
            lines.append(f"  {idx}. {step}")
        lines.append("")

    # 5. Error & Fault Instructions
    lines.append("-" * 80)
    lines.append(s["error_fault"]["title"])
    lines.append("-" * 80)
    for item in s["error_fault"]["items"]:
        lines.append(f"Problem: {item['problem']}")
        lines.append(f"  --> Possible Cause:     {item['possible_cause']}")
        lines.append(f"  --> What to Check:      {item['what_to_check']}")
        lines.append(f"  --> Recommended Action: {item['recommended_action']}")
        lines.append("")

    # 6. Maintenance Instructions
    lines.append("-" * 80)
    lines.append(s["maintenance"]["title"])
    lines.append("-" * 80)
    lines.append("[Regular Inspection]")
    for r in s["maintenance"]["regular_inspection"]:
        lines.append(f"  * {r}")
    lines.append("\n[Cleaning]")
    for cl in s["maintenance"]["cleaning"]:
        lines.append(f"  * {cl}")
    lines.append("\n[Lubrication]")
    for lb in s["maintenance"]["lubrication"]:
        lines.append(f"  * {lb}")
    lines.append("\n[Component Inspection]")
    for ci in s["maintenance"]["component_inspection"]:
        lines.append(f"  * {ci}")
    lines.append("\n[Replacement Instructions]")
    for ri in s["maintenance"]["replacement_instructions"]:
        lines.append(f"  * {ri}")
    lines.append("\n[Maintenance Intervals]")
    for mi in s["maintenance"]["maintenance_intervals"]:
        lines.append(f"  - {mi['interval']}: {mi['task']}")
    lines.append("")

    # 7. Troubleshooting Table
    lines.append("-" * 80)
    lines.append(s["troubleshooting"]["title"])
    lines.append("-" * 80)
    for row in s["troubleshooting"]["table"]:
        lines.append(f"Error / Fault: {row['error']}")
        lines.append(f"  Possible Cause: {row['possible_cause']}")
        lines.append(f"  Solution:       {row['solution']}")
        lines.append("")

    # 8. Emergency Procedures
    lines.append("-" * 80)
    lines.append(s["emergency_procedures"]["title"])
    lines.append("-" * 80)
    for ep in s["emergency_procedures"]["procedures"]:
        lines.append(f"Situation: {ep['situation']}")
        lines.append(f"  Action:    {ep['action']}")
        lines.append("")

    # 9. Technical Specifications
    lines.append("-" * 80)
    lines.append(s["specifications"]["title"])
    lines.append("-" * 80)
    for spec in s["specifications"]["specs"]:
        lines.append(f"  {spec['parameter']:<35} : {spec['value']}")
    lines.append("")

    return "\n".join(lines)


def main():
    out_dir = os.path.join(ROOT, "data", "manuals")
    os.makedirs(out_dir, exist_ok=True)

    # 1. Individual separate TXT files per language
    file_map = {
        "en": "multilingual_manual_en.txt",
        "zh": "multilingual_manual_zh.txt",
        "ja": "multilingual_manual_ja.txt",
        "de": "multilingual_manual_de.txt",
    }

    for lang, filename in file_map.items():
        data = MULTILINGUAL_MANUAL[lang]
        txt = manual_to_formatted_text(data)
        out_path = os.path.join(out_dir, filename)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(txt)
        print(f"Created: {out_path} ({len(txt)} chars)")

    # 2. Combined unified TXT file containing all 4 languages with clear separation
    combined_path = os.path.join(out_dir, "multilingual_manual.txt")
    with open(combined_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("MULTILINGUAL MACHINE INSTRUCTION MANUAL (MODEL MX-7 PRECISION)\n")
        f.write("LANGUAGES: English | Simplified Chinese (中文) | Japanese (日本語) | German (Deutsch)\n")
        f.write("=" * 80 + "\n\n")

        for lang in ["en", "zh", "ja", "de"]:
            data = MULTILINGUAL_MANUAL[lang]
            f.write("\n" + "#" * 80 + "\n")
            f.write(f"# LANGUAGE: {data['language_label'].upper()} ({lang.upper()})\n")
            f.write("#" * 80 + "\n\n")
            f.write(manual_to_formatted_text(data))
            f.write("\n\n")

    print(f"Created combined manual: {combined_path}")


if __name__ == "__main__":
    main()
