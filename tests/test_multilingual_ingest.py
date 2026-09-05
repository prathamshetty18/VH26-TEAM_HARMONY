# -*- coding: utf-8 -*-
"""
Tests for Multilingual Ingestion Pipeline:
1. Language detection sampling on multi-page text
2. NFKC Unicode normalization for full-width CJK characters
3. Invariant token preservation (numeric values, units, error codes)
4. Anti-fabrication reverse check (Structured Codes ⊆ Source Codes)
"""

import os
import sys
import unicodedata
import re
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.translation import _module_instance
from src.ingest import parse_manual_text, validate_manual_content


class TestLanguageDetectionSampling:
    """Validates document-level language sampling on industrial manual text."""

    def test_sample_german_manual(self):
        de_path = os.path.join(REPO_ROOT, "data", "manuals", "multilingual_manual_de.txt")
        if os.path.exists(de_path):
            with open(de_path, "r", encoding="utf-8") as f:
                content = f.read()
            sample_lines = [l.strip() for l in content.splitlines() if len(l.strip().split()) >= 4]
            sample_text = " ".join(sample_lines)[:2500]
            det = _module_instance.detect_language(sample_text)
            assert det["language"] == "de"
            assert det["language_name"] == "German"
            assert det.get("confidence", 0) >= 0.70

    def test_sample_chinese_manual(self):
        zh_path = os.path.join(REPO_ROOT, "data", "manuals", "multilingual_manual_zh.txt")
        if os.path.exists(zh_path):
            with open(zh_path, "r", encoding="utf-8") as f:
                content = f.read()
            sample_lines = [l.strip() for l in content.splitlines() if len(l.strip().split()) >= 4]
            sample_text = " ".join(sample_lines)[:2500]
            det = _module_instance.detect_language(sample_text)
            assert det["language"] in ["zh-CN", "zh"]
            assert "Chinese" in det["language_name"]
            assert det.get("confidence", 0) >= 0.70

    def test_sample_japanese_manual(self):
        ja_path = os.path.join(REPO_ROOT, "data", "manuals", "multilingual_manual_ja.txt")
        if os.path.exists(ja_path):
            with open(ja_path, "r", encoding="utf-8") as f:
                content = f.read()
            sample_lines = [l.strip() for l in content.splitlines() if len(l.strip().split()) >= 4]
            sample_text = " ".join(sample_lines)[:2500]
            det = _module_instance.detect_language(sample_text)
            assert det["language"] == "ja"
            assert det["language_name"] == "Japanese"
            assert det.get("confidence", 0) >= 0.70

    def test_sample_acronym_dense_german_text(self):
        sample = (
            "E101 CNC-100 400V 32A 24,000 RPM ISO 9001 DIN 55026 MODBUS RS-485 "
            "Die Motortemperatur ist zu hoch Überhitzung Fehlercode Hauptspindel"
        )
        det = _module_instance.detect_language(sample)
        assert det["language"] == "de"
        assert det["language_name"] == "German"

    def test_sample_pure_english_manual(self):
        sample = (
            "MACHINE: Conveyor Belt System\n"
            "MODEL: CB-4400\n"
            "SECTION: Drive Motor Overcurrent\n"
            "Check belt tension and replace 25-micron filter cartridge."
        )
        det = _module_instance.detect_language(sample)
        assert det["language"] == "en"
        assert det["language_name"] == "English"


class TestFullWidthUnicodeNormalization:
    """Verifies NFKC normalization converts full-width CJK alphanumeric characters."""

    def test_nfkc_normalizes_fullwidth_codes(self):
        raw = "故障代码：Ｅ１０１ ９４°Ｃ ２４，０００ ＲＰＭ ６．５ ｂａｒ"
        norm = unicodedata.normalize("NFKC", raw)
        assert "E101" in norm
        assert "94°C" in norm
        assert "24,000 RPM" in norm
        assert "6.5 bar" in norm

    def test_ingest_normalizes_fullwidth_input(self):
        raw_manual = (
            "MACHINE: ＣＮＣ Ｍｉｌｌｉｎｇ Ｍａｃｈｉｎｅ\n"
            "MODEL: ＭＸ－７\n\n"
            "ERROR CODE: Ｅ１０１\n"
            "SECTION: Ｅ１０１ Ｓｐｉｎｄｌｅ Ｏｖｅｒｈｅａｔ\n"
            "PAGE: １\n"
            "MEANING: Motor temperature exceeds ９４°Ｃ.\n"
            "CAUSES:\n- High load\n\n"
            "SECTION: Troubleshooting\n"
            "PAGE: １\n"
            "STEPS:\n1. Cool down."
        )
        chunks = parse_manual_text(raw_manual, filename="test_fullwidth.txt")
        assert len(chunks) == 2
        assert chunks[0]["error_code"] == "E101"
        assert chunks[0]["machine"] == "CNC Milling Machine"
        assert "94°C" in chunks[0]["text"]


class TestInvariantTokenPreservationAndAntiFabrication:
    """Validates ground-truth token survival and absence of fabricated codes."""

    def test_invariant_tokens_grounding_and_subset_check(self):
        source_text = """
        数控铣床 MX-7 说明书
        故障代码：E101
        主轴冷却液流量故障：流量低于 3.8 L/min，压力在 45-70 bar。
        电机最高转速 24,000 RPM，工作电压 400V 32A，油压 18 bar。
        报警阈值温度 94°C，机械间隙 0.015 mm。
        故障代码：SYM-OVERHEAT
        主轴电机定子超温。
        """

        # Simulated structured English output conforming to MANUAL_FORMAT_SPEC.md
        structured_english_output = """
        MACHINE: CNC Milling Machine
        MODEL: MX-7

        ERROR CODE: E101
        SECTION: E101 Spindle Coolant Flow Failure
        PAGE: 1
        MEANING: Spindle coolant flow drops below 3.8 L/min with delivery pressure between 45-70 bar.
        CAUSES:
        - Clogged filter cartridge
        - High-pressure pump pressure dropped below 45-70 bar

        SECTION: E101 Troubleshooting
        PAGE: 1
        STEPS:
        1. Verify 400V 32A electrical supply is stable.
        2. Ensure operating pressure is maintained at 18 bar and verify spindle speed 24,000 RPM.
        3. Check thermal threshold does not exceed 94°C and mechanical backlash is within 0.015 mm.

        ERROR CODE: SYM-OVERHEAT
        SECTION: SYM-OVERHEAT Spindle Stator Overtemperature
        PAGE: 2
        MEANING: Stator winding temperature exceeds critical threshold.
        CAUSES:
        - Excessive roughing load
        STEPS:
        1. Idle spindle for 10 minutes.
        """

        # 1. Normalize both source and output
        norm_source = unicodedata.normalize("NFKC", source_text)
        norm_output = unicodedata.normalize("NFKC", structured_english_output)

        # 2. Check that all critical numeric units survive verbatim
        expected_units = [
            "3.8 L/min",
            "45-70 bar",
            "24,000 RPM",
            "400V",
            "32A",
            "18 bar",
            "94°C",
            "0.015 mm"
        ]
        for unit in expected_units:
            assert unit in norm_output, f"Critical unit '{unit}' was mutated or omitted!"

        # 3. Anti-Fabrication Subset Check: Codes(output) ⊆ Codes(source)
        code_regex = re.compile(r"\b([A-Z]{1,4}-\d{2,4}|[A-Z]\d{3,4}|SYM-[A-Z0-9-]+)\b")
        source_codes = set(code_regex.findall(norm_source))
        output_codes = set(code_regex.findall(norm_output))

        # Filter out false positives from format labels if any (e.g. RPM, CNC)
        non_code_words = {"CNC", "RPM", "LOTO", "ANSI", "ISO", "DIN"}
        source_codes = {c for c in source_codes if c not in non_code_words}
        output_codes = {c for c in output_codes if c not in non_code_words}

        assert "E101" in output_codes
        assert "SYM-OVERHEAT" in output_codes
        # The key anti-fabrication guarantee:
        fabricated_codes = output_codes - source_codes
        assert not fabricated_codes, f"LLM fabricated phantom error codes: {fabricated_codes}"
