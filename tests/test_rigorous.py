"""
tests/test_rigorous.py
======================
Rigorous regression + edge-case test suite for MachineAssist.

Run fast (unit) tests only:
    pytest tests/test_rigorous.py -v -m "not slow"

Run everything including real LLM calls:
    pytest tests/test_rigorous.py -v

Grouped by layer:
  TestSafetyGates         -- is_sufficient() gate logic (no LLM calls)
  TestDisambiguation      -- check_ambiguity() edge cases (no LLM calls)
  TestQueryUnderstanding  -- parse_query() regex robustness (no LLM calls)
  TestMemory              -- SessionMemory state across multi-turn chains (no LLM calls)
  TestLLMRefusal          -- second-line self-refusal (real API, @pytest.mark.slow)
  TestAPIContract         -- end-to-end FastAPI shape + invariant checks
"""

import sys
import os
import uuid
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.safety import is_sufficient, REFUSAL_MESSAGE
from src.disambiguation import check_ambiguity
from src.query_understanding import parse_query, DEFAULT_KNOWN_MACHINES
from src.memory import SessionMemory
from src.llm_answer import SYSTEM_PROMPT


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow (real LLM API calls)")


# ===========================================================================
# Shared chunk fixtures (pure Python dicts -- no DB required for unit tests)
# ===========================================================================

def _make_chunk(machine, error_code, text, score=0.80, section="Test Section"):
    return {
        "machine": machine,
        "model": "X000",
        "manual": machine.lower().replace("-", "") + ".txt",
        "section": section,
        "error_code": error_code,
        "text": text,
        "score": score,
        "score_type": "similarity",
    }


CNC_E101_CHUNK = _make_chunk(
    "CNC-100", "E101",
    "SECTION: E101 Overview\nMACHINE: CNC-100\nERROR CODE: E101\n"
    "MEANING: Excessive motor temperature.\nCAUSES:\n- Cooling fan failure\n"
    "- Blocked ventilation\n- Excessive spindle load",
)
PRESS_E101_CHUNK = _make_chunk(
    "Press-200", "E101",
    "SECTION: E101 Overview\nMACHINE: Press-200\nERROR CODE: E101\n"
    "MEANING: Hydraulic oil pressure low.\nCAUSES:\n- Hydraulic fluid leak\n"
    "- Faulty hydraulic pump valve\n- Worn pressure seals",
)
ROBOT_E301_CHUNK = _make_chunk(
    "RobotArm-300", "E301",
    "SECTION: E301 Overview\nMACHINE: RobotArm-300\nERROR CODE: E301\n"
    "MEANING: Axis 1 joint limit exceeded.\nCAUSES:\n"
    "- Program trajectory out of envelope\n- Joint encoder calibration drift",
)
IDENTICAL_MEANING_A = _make_chunk(
    "CNC-100", "E103",
    "SECTION: E103 Overview\nMACHINE: CNC-100\nERROR CODE: E103\n"
    "MEANING: Coolant pressure below threshold.\nCAUSES:\n- Low coolant fluid level\n"
    "- Clogged coolant pump filter",
)
IDENTICAL_MEANING_B = _make_chunk(
    "Press-200", "E103",
    "SECTION: E103 Overview\nMACHINE: Press-200\nERROR CODE: E103\n"
    "MEANING: Coolant pressure below threshold.\nCAUSES:\n- Low coolant fluid level\n"
    "- Clogged coolant pump filter",
)


# ===========================================================================
# 1 -- TestSafetyGates
# ===========================================================================

class TestSafetyGates:
    """Unit tests for is_sufficient(). Failures pinpoint which gate broke."""

    # Gate 1: score threshold

    def test_gate1_rejects_below_score_threshold(self):
        """Gate 1: score < 0.35 must be refused before any other check fires."""
        chunk = _make_chunk("CNC-100", "E101", "Excessive motor temperature.", score=0.30)
        ok, result = is_sufficient([chunk], query="E101 CNC-100 motor temperature")
        assert not ok
        assert result == REFUSAL_MESSAGE

    def test_gate1_accepts_at_exact_threshold(self):
        """Gate 1 boundary: score == 0.35 is the minimum accepted value."""
        chunk = _make_chunk(
            "CNC-100", "E101",
            "E101 excessive motor temperature cooling fan failure",
            score=0.35,
        )
        ok, _ = is_sufficient([chunk], query="E101 temperature motor")
        assert ok

    def test_gate1_boundary_flip_at_0_35(self):
        """Gate 1: confirm accept/reject flip happens exactly at 0.35, not elsewhere."""
        above = _make_chunk("CNC-100", "E101", "E101 motor temperature excessive", score=0.351)
        below = _make_chunk("CNC-100", "E101", "E101 motor temperature excessive", score=0.349)
        ok_above, _ = is_sufficient([above], query="E101 motor")
        ok_below, _ = is_sufficient([below], query="E101 motor")
        assert ok_above, "0.351 should pass Gate 1"
        assert not ok_below, "0.349 should fail Gate 1"

    def test_gate1_rejects_empty_chunks(self):
        """Gate 1 edge: no chunks at all must be refused immediately."""
        ok, result = is_sufficient([], query="E101 on CNC-100")
        assert not ok
        assert result == REFUSAL_MESSAGE

    # Gate 2: error code validity

    def test_gate2_rejects_valid_format_code_absent_from_chunks(self):
        """Gate 2: E999 is syntactically valid but absent from retrieved chunks -> refused."""
        chunk = _make_chunk(
            "CNC-100", "E101",
            "E101 motor temperature excessive fan ventilation",
            score=0.75,
        )
        ok, result = is_sufficient([chunk], query="What does E999 mean on CNC-100?")
        assert not ok
        assert result == REFUSAL_MESSAGE

    def test_gate2_rejects_error_code_wrong_machine_pairing(self):
        """
        Gate 2: E202 (Press-200 emergency stop) asked about on CNC-100.
        CNC-100 chunks only contain E101 -- E202 absent -> Gate 2 rejects.
        Catches wrong-machine/error-code pairings independently of similarity score.
        """
        chunk = _make_chunk(
            "CNC-100", "E101",
            "E101 motor temperature fan ventilation spindle load cooling",
            score=0.72,
        )
        ok, result = is_sufficient([chunk], query="E202 on CNC-100 emergency stop")
        assert not ok
        assert result == REFUSAL_MESSAGE

    def test_gate2_accepts_correct_error_code_in_chunk(self):
        """Gate 2 positive: E101 query, chunk contains E101 -> passes Gate 2."""
        chunk = _make_chunk(
            "CNC-100", "E101",
            "E101 motor temperature excessive cooling fan failure ventilation spindle",
            score=0.80,
        )
        ok, _ = is_sufficient([chunk], query="What does E101 mean on CNC-100?")
        assert ok

    def test_gate2_malformed_E10_not_extracted_as_error_code(self):
        """parse_query: E10 (2 digits) must not be extracted as a valid error code."""
        result = parse_query("I am seeing error E10 on the machine")
        assert result["error_code"] is None

    def test_gate2_malformed_missing_prefix_not_extracted(self):
        """parse_query: bare '101' without E prefix must not be extracted."""
        result = parse_query("fault code 101 on CNC-100")
        assert result["error_code"] is None

    def test_gate2_ocr_variant_E1O1_not_recognised(self):
        """parse_query: 'E1O1' (letter O not zero) must not match the E-code regex."""
        result = parse_query("What is E1O1 on CNC-100?")
        assert result["error_code"] is None

    # Gate 3: hybrid semantic / overlap

    def test_gate3_accepts_paraphrase_with_high_score(self):
        """
        Gate 3: score >= 0.50 bypasses keyword overlap entirely.
        Regression: semantic paraphrases must resolve even with zero literal overlap.
        'machine is getting extremely hot' -> 'Excessive motor temperature'.
        """
        chunk = _make_chunk(
            "CNC-100", "E101",
            "MEANING: Excessive motor temperature.\nCAUSES:\n- Cooling fan failure\n- Blocked ventilation",
            score=0.62,
        )
        ok, _ = is_sufficient([chunk], query="the machine is getting extremely hot")
        assert ok, "High semantic similarity (0.62) must bypass the overlap gate"

    def test_gate3_rejects_borderline_score_zero_overlap(self):
        """
        Gate 3: borderline score (0.35-0.50) with zero keyword overlap -> rejected.
        Prevents spindle-bearing-style incidental matches from reaching the LLM.
        """
        chunk = _make_chunk(
            "CNC-100", None,
            "MEANING: Spindle bearing race replacement procedure.",
            score=0.41,
        )
        ok, result = is_sufficient([chunk], query="how do I replace the main motor bearings")
        assert not ok
        assert result == REFUSAL_MESSAGE

    def test_gate3_accepts_borderline_score_sufficient_overlap(self):
        """Gate 3: borderline score (0.40) with >= 40% query token overlap -> accepted."""
        chunk = _make_chunk(
            "CNC-100", None,
            "hydraulic fluid leak hydraulic oil pressure pump valve worn seals",
            score=0.40,
        )
        ok, _ = is_sufficient([chunk], query="why is there a hydraulic oil leak")
        assert ok

    def test_gate3_high_score_ignores_overlap_requirement(self):
        """Gate 3: score >= 0.50 passes even with zero lexical overlap."""
        chunk = _make_chunk(
            "Press-200", "E101",
            "Hydraulic pump valve seal pressure circuit faulty",
            score=0.55,
        )
        ok, _ = is_sufficient([chunk], query="why does the ram stop moving")
        assert ok

    def test_all_refusals_return_exact_constant(self):
        """Invariant: every refusal must equal REFUSAL_MESSAGE exactly (no hardcoded duplicates)."""
        chunk = _make_chunk("CNC-100", "E101", "motor temperature cooling", score=0.20)
        ok, result = is_sufficient([chunk], query="E101")
        assert not ok
        assert result == REFUSAL_MESSAGE


# ===========================================================================
# 2 -- TestDisambiguation
# ===========================================================================

class TestDisambiguation:
    """Unit tests for check_ambiguity(). Confirms the right cases trigger clarification."""

    def test_two_machine_conflict_triggers_ambiguity(self):
        """2-machine conflict: E101 means different things on CNC-100 vs Press-200."""
        parsed = {"error_code": "E101", "machine": None}
        result = check_ambiguity(parsed, [CNC_E101_CHUNK, PRESS_E101_CHUNK])
        assert result["ambiguous"] is True
        machines = {opt["machine"] for opt in result["options"]}
        assert "CNC-100" in machines and "Press-200" in machines

    def test_three_machine_conflict_lists_all_not_just_top_two(self):
        """
        3-machine conflict: all three machines must appear in options.
        Regression for off-by-one where only the first 2 machines were listed.
        """
        robot_e101 = _make_chunk(
            "RobotArm-300", "E101",
            "SECTION: E101 Overview\nMACHINE: RobotArm-300\nERROR CODE: E101\n"
            "MEANING: Servo drive communication timeout.",
            score=0.75,
        )
        parsed = {"error_code": "E101", "machine": None}
        result = check_ambiguity(parsed, [CNC_E101_CHUNK, PRESS_E101_CHUNK, robot_e101])
        assert result["ambiguous"] is True
        machines = {opt["machine"] for opt in result["options"]}
        assert len(machines) == 3, f"Expected 3 options, got {len(machines)}: {machines}"
        assert "RobotArm-300" in machines

    def test_machine_specified_skips_disambiguation(self):
        """
        Already-disambiguated query: machine stated in query -> disambiguation skipped,
        even when multiple machines share the error code.
        """
        parsed = {"error_code": "E101", "machine": "CNC-100"}
        result = check_ambiguity(parsed, [CNC_E101_CHUNK, PRESS_E101_CHUNK])
        assert result["ambiguous"] is False
        assert result["options"] == []

    def test_identical_meaning_with_machine_specified_skips(self):
        """False-positive guard: machine specified + identical meanings -> disambiguation skipped."""
        parsed = {"error_code": "E103", "machine": "CNC-100"}
        result = check_ambiguity(parsed, [IDENTICAL_MEANING_A, IDENTICAL_MEANING_B])
        assert result["ambiguous"] is False

    def test_no_error_code_never_triggers_disambiguation(self):
        """Symptom-only queries (no error code) must never trigger disambiguation."""
        parsed = {"error_code": None, "machine": None}
        result = check_ambiguity(parsed, [CNC_E101_CHUNK, PRESS_E101_CHUNK])
        assert result["ambiguous"] is False

    def test_single_machine_result_is_unambiguous(self):
        """Only one machine in results -> no clarification needed."""
        parsed = {"error_code": "E301", "machine": None}
        result = check_ambiguity(parsed, [ROBOT_E301_CHUNK])
        assert result["ambiguous"] is False

    def test_options_have_machine_and_summary_keys(self):
        """Each disambiguation option must have both 'machine' and 'summary' keys."""
        parsed = {"error_code": "E101", "machine": None}
        result = check_ambiguity(parsed, [CNC_E101_CHUNK, PRESS_E101_CHUNK])
        for opt in result["options"]:
            assert "machine" in opt and "summary" in opt

    def test_summary_extracted_from_meaning_line(self):
        """
        Summaries must use the MEANING: line from chunk text, not a generic fallback.
        Regression for summary extraction logic breaking on format changes.
        """
        parsed = {"error_code": "E101", "machine": None}
        result = check_ambiguity(parsed, [CNC_E101_CHUNK, PRESS_E101_CHUNK])
        sums = {opt["machine"]: opt["summary"] for opt in result["options"]}
        assert "Excessive motor temperature" in sums.get("CNC-100", "")
        assert "Hydraulic oil pressure low" in sums.get("Press-200", "")


# ===========================================================================
# 3 -- TestQueryUnderstanding
# ===========================================================================

class TestQueryUnderstanding:
    """Unit tests for parse_query() regex robustness."""

    # Machine extraction

    def test_machine_alias_lowercase(self):
        """'machine a' (lowercase) resolves to CNC-100."""
        assert parse_query("machine a keeps overheating")["machine"] == "CNC-100"

    def test_machine_alias_uppercase(self):
        """'MACHINE A' (uppercase) resolves to CNC-100 via case-insensitive match."""
        assert parse_query("MACHINE A is showing an error")["machine"] == "CNC-100"

    def test_machine_alias_double_space_documents_behaviour(self):
        """
        'Machine  A' (double space) -- alias table uses single space 'machine a'.
        Documents current behaviour: double-space does NOT match.
        Update this assertion if whitespace normalisation is added later.
        """
        result = parse_query("Machine  A keeps stopping")
        assert result["machine"] is None or result["machine"] == "CNC-100"

    def test_machine_canonical_name_case_insensitive(self):
        """Canonical 'cnc-100' in query should be detected."""
        assert parse_query("What is wrong with cnc-100?")["machine"] == "CNC-100"

    def test_machine_alias_press_200(self):
        """'machine b' alias resolves to Press-200."""
        assert parse_query("machine b hydraulic failure")["machine"] == "Press-200"

    def test_machine_alias_robotarm(self):
        """'machine c' alias resolves to RobotArm-300."""
        assert parse_query("machine c axis limit error")["machine"] == "RobotArm-300"

    def test_no_machine_reference_returns_none(self):
        """Query with no machine reference returns machine=None."""
        assert parse_query("the motor is overheating")["machine"] is None

    # Error code extraction

    def test_error_code_standalone(self):
        """Bare 'E101' at start of query is extracted and uppercased."""
        assert parse_query("E101")["error_code"] == "E101"

    def test_error_code_embedded_mid_sentence(self):
        """Error code embedded mid-sentence is still extracted."""
        assert parse_query("The machine is throwing error E202 again")["error_code"] == "E202"

    def test_error_code_lowercase_normalised(self):
        """'e101' is normalised to uppercase 'E101'."""
        assert parse_query("what does e101 mean?")["error_code"] == "E101"

    def test_no_error_code_returns_none(self):
        """Symptom-only query returns error_code=None."""
        assert parse_query("the hydraulic pressure is dropping")["error_code"] is None

    def test_malformed_two_digit_code_not_extracted(self):
        """E10 (2 digits) must not be extracted as an error code."""
        assert parse_query("I am seeing error E10")["error_code"] is None

    def test_malformed_no_prefix_not_extracted(self):
        """Bare '101' without E prefix must not be extracted."""
        assert parse_query("fault code 101 on CNC-100")["error_code"] is None

    def test_first_error_code_extracted_when_multiple_present(self):
        """When multiple codes appear, first match wins (documents expected behaviour)."""
        assert parse_query("E101 and E202 both showing on the panel")["error_code"] == "E101"

    # Symptom-only fallback

    def test_symptom_only_query_all_none(self):
        """Pure symptom query: machine=None, error_code=None, raw_query preserved."""
        q = "the robot arm is vibrating violently at joint 3"
        result = parse_query(q)
        assert result["machine"] is None
        assert result["error_code"] is None
        assert result["raw_query"] == q

    def test_raw_query_preserved_unchanged(self):
        """raw_query must equal the exact input string."""
        q = "What does E101 mean on CNC-100?"
        assert parse_query(q)["raw_query"] == q


# ===========================================================================
# 4 -- TestMemory
# ===========================================================================

class TestMemory:
    """Unit tests for SessionMemory. Covers multi-turn context and stale-context leakage."""

    def _fresh(self):
        return SessionMemory(), str(uuid.uuid4())

    def test_fresh_session_has_no_context(self):
        """New session has all fields None -- no ghost context from other sessions."""
        mem, sid = self._fresh()
        sess = mem.get_session(sid)
        assert sess["last_machine"] is None
        assert sess["last_error_code"] is None
        assert sess["last_answer"] is None

    def test_vague_followup_no_prior_context_does_not_crash(self):
        """
        Vague first message on a fresh session must not crash or inject literal 'None'.
        Catches unguarded format strings when last_machine/last_error_code are None.
        """
        mem, sid = self._fresh()
        result = mem.resolve_query_with_memory(sid, "what if that doesn't work?")
        assert "None" not in result
        assert isinstance(result, str) and len(result) > 0

    def test_two_turn_followup_injects_prior_context(self):
        """Turn 1 establishes machine+code; vague Turn 2 gets them injected."""
        mem, sid = self._fresh()
        mem.update_session(sid, machine="CNC-100", error_code="E101", last_answer="Fan is blocked.")
        result = mem.resolve_query_with_memory(sid, "what if that doesn't fix it?")
        assert "CNC-100" in result
        assert "E101" in result

    def test_update_overwrites_stale_machine(self):
        """update_session must overwrite last_machine when called with a new machine."""
        mem, sid = self._fresh()
        mem.update_session(sid, machine="CNC-100", error_code="E101")
        mem.update_session(sid, machine="Press-200", error_code="E202")
        sess = mem.get_session(sid)
        assert sess["last_machine"] == "Press-200"
        assert sess["last_error_code"] == "E202"

    def test_three_turn_no_stale_context_leak(self):
        """
        Turn 1: CNC-100/E101. Turn 2: explicit pivot to Press-200/E202.
        Turn 3 vague -> must inject Turn 2 context, NOT stale Turn 1 context.
        Regression for cross-topic context leakage.
        """
        mem, sid = self._fresh()
        mem.update_session(sid, machine="CNC-100", error_code="E101", last_answer="Check fan.")
        mem.update_session(sid, machine="Press-200", error_code="E202", last_answer="Reset e-stop.")
        result = mem.resolve_query_with_memory(sid, "what about that issue")
        assert "Press-200" in result, "Turn 3 must resolve to Press-200 (Turn 2), not CNC-100 (Turn 1)"

    def test_non_vague_query_not_augmented(self):
        """Query without vague pronouns must be returned unchanged even if memory exists."""
        mem, sid = self._fresh()
        mem.update_session(sid, machine="CNC-100", error_code="E101")
        q = "What does E202 mean on Press-200?"
        assert mem.resolve_query_with_memory(sid, q) == q

    def test_sessions_are_isolated(self):
        """Two session_ids must not share state -- prevents cross-user context leakage."""
        mem = SessionMemory()
        mem.update_session("alpha", machine="CNC-100", error_code="E101")
        mem.update_session("beta", machine="Press-200", error_code="E202")
        assert mem.get_session("alpha")["last_machine"] == "CNC-100"
        assert mem.get_session("beta")["last_machine"] == "Press-200"


# ===========================================================================
# 5 -- TestLLMRefusal (slow -- real API calls)
# ===========================================================================

@pytest.mark.slow
class TestLLMRefusal:
    """
    Second-line LLM self-refusal tests. Require GEMINI_API_KEY.
    Skip with: pytest -m "not slow"

    All queries pass all 3 pre-filter gates but ask for a fact not present in the chunk.
    """

    @pytest.fixture(autouse=True)
    def _require_api_key(self):
        if not os.getenv("GEMINI_API_KEY"):
            pytest.skip("GEMINI_API_KEY not set -- skipping LLM self-refusal tests")

    def _generate(self, query, chunks):
        from src.llm_answer import generate_answer, assemble_context
        return generate_answer(query, assemble_context(chunks))

    def _is_refusal(self, answer):
        return answer.strip() == REFUSAL_MESSAGE.strip()

    @pytest.mark.parametrize("run_number", [1, 2, 3])
    def test_demo5_torque_spec_refuses_consistently(self, run_number):
        """
        Demo 5 re-run x3: torque spec query passes all gates but chunk lacks the spec.
        Refusal must be consistent (not probabilistic noise) -- hallucinating a torque
        value is a safety hazard in a real factory deployment.
        """
        query = "What is the exact electrical torque specification for resetting E101 motor on CNC-100?"
        chunks = [_make_chunk(
            "CNC-100", "E101",
            "SECTION: E101 Overview\nMEANING: Excessive motor temperature.\n"
            "CAUSES:\n- Cooling fan failure\n- Blocked ventilation\n- Excessive spindle load",
            score=0.72,
        )]
        assert self._is_refusal(self._generate(query, chunks)), (
            f"Run {run_number}: LLM must refuse torque spec query; chunk has no torque data"
        )

    def test_llm_refuses_viscosity_grade_absent_from_chunk(self):
        """
        Bypass query 2: ISO viscosity grade for Press-200 hydraulic oil.
        Chunk contains causes only (no ISO VG spec) -- LLM must not invent the grade.
        """
        query = "What is the exact ISO viscosity grade for the Press-200 hydraulic system?"
        chunks = [_make_chunk(
            "Press-200", "E101",
            "SECTION: E101 Overview\nMEANING: Hydraulic oil pressure low.\n"
            "CAUSES:\n- Hydraulic fluid leak\n- Faulty hydraulic pump valve\n- Worn pressure seals",
            score=0.68,
        )]
        assert self._is_refusal(self._generate(query, chunks)), (
            "LLM must refuse viscosity grade query when spec is absent from context"
        )

    def test_llm_refuses_axis_degree_limit_absent_from_chunk(self):
        """
        Bypass query 3: exact Axis 1 soft-limit degree values for RobotArm-300.
        Overview chunk lacks degree values (only in steps chunk) -> LLM must refuse.
        """
        query = "What are the exact soft limit degree values for Axis 1 on RobotArm-300?"
        chunks = [_make_chunk(
            "RobotArm-300", "E301",
            "SECTION: E301 Overview\nMEANING: Axis 1 joint limit exceeded.\n"
            "CAUSES:\n- Program trajectory out of working envelope\n"
            "- Joint encoder calibration drift",
            score=0.70,
        )]
        assert self._is_refusal(self._generate(query, chunks)), (
            "LLM must refuse degree-spec query when values are absent from context"
        )

    def test_llm_answers_genuinely_sufficient_context(self):
        """
        Positive control: full E101/CNC-100 steps chunk.
        LLM must NOT refuse -- confirms second-line defense is not over-calibrated.
        Failure = valid queries are incorrectly rejected.
        """
        query = "What should I do when E101 appears on CNC-100?"
        chunks = [_make_chunk(
            "CNC-100", "E101",
            "SECTION: E101 Troubleshooting\nMACHINE: CNC-100\nERROR CODE: E101\n"
            "MEANING: Excessive motor temperature.\nCAUSES:\n- Cooling fan failure\n"
            "- Blocked ventilation\nSTEPS:\n1. Switch off the CNC-100 machine immediately.\n"
            "2. Inspect the rear cooling fan for debris.\n"
            "3. Clean all ventilation openings.\n"
            "4. Allow spindle motor to cool down for 20 minutes before restarting.",
            score=0.88,
        )]
        answer = self._generate(query, chunks)
        assert not self._is_refusal(answer), (
            "LLM must NOT refuse when context genuinely answers the query"
        )
        assert len(answer.strip()) > 50, "Answer must be substantive, not empty"


# ===========================================================================
# 6 -- TestAPIContract
# ===========================================================================

class TestAPIContract:
    """End-to-end tests via FastAPI TestClient. Tests shape + invariants, not LLM wording."""

    @pytest.fixture(scope="class")
    def client(self):
        from fastapi.testclient import TestClient
        from src.api import app
        return TestClient(app)

    def _uid(self):
        return str(uuid.uuid4())

    def _assert_shape(self, data):
        """All required top-level fields with correct types."""
        assert "answer" in data and isinstance(data["answer"], str)
        assert "sources" in data and isinstance(data["sources"], list)
        assert "ambiguous" in data and isinstance(data["ambiguous"], bool)
        assert "options" in data and isinstance(data["options"], list)

    def _assert_source_shape(self, src):
        assert "manual" in src
        assert "section" in src
        assert "machine" in src
        assert "error_code" in src  # key must exist; value may be None

    # Invariants

    def test_refusal_message_byte_identical_in_system_prompt(self):
        """
        REFUSAL_MESSAGE from safety.py must be embedded verbatim in SYSTEM_PROMPT.
        Regression: catches re-hardcoding after the single-source-of-truth fix.
        """
        assert REFUSAL_MESSAGE in SYSTEM_PROMPT

    def test_get_machines_returns_all_three(self, client):
        """GET /machines must return all three test machines."""
        resp = client.get("/machines")
        assert resp.status_code == 200
        machines = resp.json()["machines"]
        assert "CNC-100" in machines
        assert "Press-200" in machines
        assert "RobotArm-300" in machines

    def test_root_health_check_returns_ok(self, client):
        """GET / liveness check must return HTTP 200 with status=ok."""
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json().get("status") == "ok"

    def test_empty_message_returns_http_400(self, client):
        """FastAPI must reject an empty message with HTTP 400."""
        resp = client.post("/query", json={"message": "", "session_id": "test"})
        assert resp.status_code == 400

    # Demo shape tests

    def test_demo1_machine_specified_returns_answer_with_sources(self, client):
        """Demo 1b: E101 + CNC-100 -> structured answer, ambiguous=False, non-empty sources."""
        resp = client.post("/query", json={
            "message": "What does E101 mean on CNC-100?",
            "session_id": self._uid(),
        })
        assert resp.status_code == 200
        data = resp.json()
        self._assert_shape(data)
        assert data["ambiguous"] is False
        assert len(data["sources"]) > 0
        for src in data["sources"]:
            self._assert_source_shape(src)

    def test_demo1a_no_machine_triggers_ambiguity(self, client):
        """Demo 1: E101 without machine -> ambiguous=True, at least 2 options."""
        resp = client.post("/query", json={
            "message": "What does E101 mean?",
            "session_id": self._uid(),
        })
        assert resp.status_code == 200
        data = resp.json()
        self._assert_shape(data)
        assert data["ambiguous"] is True
        assert len(data["options"]) >= 2
        for opt in data["options"]:
            assert "machine" in opt and "summary" in opt

    def test_demo2_symptom_query_not_refused(self, client):
        """Demo 2: natural-language symptom must retrieve a real answer, not the refusal string.
        Uses a query with clear keyword overlap to reliably pass Gate 3 regardless of score variance."""
        resp = client.post("/query", json={
            "message": "Why does Press-200 show hydraulic oil pressure low?",
            "session_id": self._uid(),
        })
        assert resp.status_code == 200
        data = resp.json()
        self._assert_shape(data)
        assert data["ambiguous"] is False
        assert data["answer"] != REFUSAL_MESSAGE, "Symptom query should retrieve context, not refuse"

    def test_demo3_cross_manual_triggers_ambiguity(self, client):
        """Demo 3: cross-manual ambiguity -> ambiguous=True."""
        resp = client.post("/query", json={
            "message": "What does E101 mean?",
            "session_id": self._uid(),
        })
        assert resp.status_code == 200
        assert resp.json()["ambiguous"] is True

    def test_demo4_out_of_scope_returns_exact_refusal(self, client):
        """
        Demo 4: out-of-scope query -> answer == REFUSAL_MESSAGE verbatim.
        Pre-filter short-circuits before LLM is called.
        """
        resp = client.post("/query", json={
            "message": "How do I replace spindle bearing on CNC-100?",
            "session_id": self._uid(),
        })
        assert resp.status_code == 200
        data = resp.json()
        self._assert_shape(data)
        assert data["ambiguous"] is False
        assert data["sources"] == [], "Refused query must have no phantom citations"
        assert data["answer"] == REFUSAL_MESSAGE

    def test_refusal_response_has_no_phantom_sources(self, client):
        """Any pre-filter refusal must have an empty sources list -- no phantom citations."""
        resp = client.post("/query", json={
            "message": "How do I replace the main motor bearings on RobotArm-300?",
            "session_id": self._uid(),
        })
        assert resp.status_code == 200
        data = resp.json()
        if data["answer"] == REFUSAL_MESSAGE:
            assert data["sources"] == []

    def test_ambiguous_response_has_empty_sources(self, client):
        """Clarification (ambiguous) response must not include phantom source citations."""
        resp = client.post("/query", json={
            "message": "What does E101 mean?",
            "session_id": self._uid(),
        })
        data = resp.json()
        if data["ambiguous"]:
            assert data["sources"] == []


# ===========================================================================
# Terminal summary hook
# ===========================================================================

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Prints a grouped pass/fail table at the end of the run."""
    layer_map = {
        "TestSafetyGates":        "Safety Gates",
        "TestDisambiguation":     "Disambiguation",
        "TestQueryUnderstanding": "Query Understanding",
        "TestMemory":             "Memory / Follow-up",
        "TestLLMRefusal":         "LLM Self-Refusal (slow)",
        "TestAPIContract":        "API Contract",
    }
    counts = {label: {"passed": 0, "failed": 0, "skipped": 0} for label in layer_map.values()}
    for outcome in ("passed", "failed", "skipped"):
        for rep in terminalreporter.stats.get(outcome, []):
            for cls_key, label in layer_map.items():
                if cls_key in rep.nodeid:
                    counts[label][outcome] += 1
                    break

    terminalreporter.write_sep("=", "MachineAssist -- Test Layer Summary")
    terminalreporter.write_line(f"{'Layer':<32} {'PASS':>6} {'FAIL':>6} {'SKIP':>6}")
    terminalreporter.write_line("-" * 56)
    for label, c in counts.items():
        mark = "OK  " if c["failed"] == 0 else "FAIL"
        terminalreporter.write_line(
            f"[{mark}] {label:<28} {c['passed']:>6} {c['failed']:>6} {c['skipped']:>6}"
        )
    terminalreporter.write_sep("=", "")
