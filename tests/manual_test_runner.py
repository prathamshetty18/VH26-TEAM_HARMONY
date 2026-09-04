#!/usr/bin/env python3
"""
Manual Test Runner for MachineAssist Troubleshooting System.
Designed for Teammate A (manual author / query tester) to run benchmark queries
against the API endpoint and track passes, failures, and infrastructure issues.
"""

import argparse
import datetime
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

# Default API endpoint configuration
DEFAULT_ENDPOINT = "http://127.0.0.1:8000/query"
DEFAULT_TIMEOUT_SEC = 30.0


def load_queries(json_path: str) -> List[Dict[str, Any]]:
    """Loads benchmark query definitions from JSON file."""
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Query file not found at: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_response(item: Dict[str, Any], status_code: int, data: Optional[Dict[str, Any]], error_msg: Optional[str]) -> Tuple[str, str]:
    """
    Evaluates API response against expected behavior.
    Returns (status, actual_summary)
    Status is one of: PASS, FAIL, MANUAL_REVIEW, INFRASTRUCTURE_FAILURE.
    """
    if error_msg:
        return "INFRASTRUCTURE_FAILURE", error_msg

    if not (200 <= status_code < 300) or not isinstance(data, dict):
        return "INFRASTRUCTURE_FAILURE", f"HTTP {status_code}: {str(data)[:100]}"

    category = item.get("category", "")
    answer = str(data.get("answer", "")).strip()
    ambiguous = data.get("ambiguous", False)
    options = data.get("options", []) or []
    sources = data.get("sources", []) or []
    forbidden_keywords = [k.lower() for k in item.get("forbidden_keywords", [])]

    # Cross-Manual Leakage Check: forbidden keywords MUST NOT appear in the answer (word-boundary matched)
    import re
    answer_lower = answer.lower()
    for fkw in forbidden_keywords:
        pattern = r"\b" + re.escape(fkw) + r"\b"
        if re.search(pattern, answer_lower):
            return "FAIL", f"CROSS-MANUAL LEAKAGE: Forbidden keyword '{fkw}' detected in answer! Answer: {answer[:140]}"

    # 1. Ambiguous Category
    if category == "ambiguous":
        if ambiguous is True and len(options) >= 2:
            opt_machines = [o.get("machine", "") for o in options]
            return "PASS", f"Ambiguous detected: {len(options)} options ({', '.join(opt_machines)})"
        elif ambiguous is True:
            return "PASS", f"Ambiguous detected ({len(options)} options)"
        else:
            return "FAIL", f"Expected ambiguous=True, got ambiguous={ambiguous}. Answer: {answer[:100]}"

    # 2. Undocumented Gap Category
    if category == "undocumented_gap":
        refusal_phrases = [
            "not provide sufficient information",
            "unsupported answer",
            "do not document",
            "no documentation",
            "insufficient information"
        ]
        is_refusal = any(p in answer_lower for p in refusal_phrases)
        if is_refusal and not sources:
            return "PASS", f"Honest refusal triggered: {answer[:120]}"
        elif is_refusal:
            return "PASS", f"Honest refusal triggered with sources: {answer[:120]}"
        else:
            return "FAIL", f"Failed to refuse undocumented query (hallucination detected). Answer: {answer[:120]}"

    # 3. Exact Code & Natural Language Categories
    if category in ("exact_code", "natural_language"):
        # If it returned a generic refusal when it should have had context, mark FAIL
        refusal_phrases = ["not provide sufficient information", "unsupported answer"]
        if any(p in answer_lower for p in refusal_phrases) and not sources:
            return "FAIL", f"Refusal returned instead of manual instructions: {answer[:120]}"

        expected_machine = (item.get("expected_machine") or "").lower()
        expected_model = (item.get("expected_model") or "").lower()
        expected_code = (item.get("expected_error_code") or "").lower()
        expected_keywords = [k.lower() for k in item.get("expected_keywords", [])]

        # Check citations and text
        full_text_to_check = answer_lower
        for s in sources:
            full_text_to_check += " " + str(s.get("manual", "")).lower()
            full_text_to_check += " " + str(s.get("section", "")).lower()
            full_text_to_check += " " + str(s.get("machine", "")).lower()
            full_text_to_check += " " + str(s.get("error_code", "")).lower()

        matched_keywords = [k for k in expected_keywords if k in full_text_to_check]
        keyword_ratio = len(matched_keywords) / len(expected_keywords) if expected_keywords else 1.0

        machine_matched = True
        if expected_machine:
            m_tokens = [t for t in expected_machine.split() if len(t) > 2]
            machine_matched = any(t in full_text_to_check for t in m_tokens) or (expected_model and expected_model in full_text_to_check)

        code_matched = True
        if expected_code and not expected_code.startswith("sym-"):
            code_matched = expected_code in full_text_to_check

        if keyword_ratio >= 0.50 and machine_matched:
            return "PASS", answer[:200]
        elif keyword_ratio > 0.0 or machine_matched or code_matched:
            return "MANUAL_REVIEW", f"Partial match ({len(matched_keywords)}/{len(expected_keywords)} kw, machine={machine_matched}): {answer[:150]}"
        else:
            return "FAIL", f"No keyword/machine match ({len(matched_keywords)}/{len(expected_keywords)} kw): {answer[:120]}"

    # Fallback
    return "MANUAL_REVIEW", answer[:200]


def run_tests(
    queries: List[Dict[str, Any]],
    endpoint: str = DEFAULT_ENDPOINT,
    timeout: float = DEFAULT_TIMEOUT_SEC,
    filter_id: Optional[str] = None,
    filter_category: Optional[str] = None,
    results_dir: str = "tests/results"
) -> Dict[str, Any]:
    """Runs tests against API endpoint and generates markdown report."""

    # Apply filters
    filtered_queries = queries
    if filter_id:
        filtered_queries = [q for q in filtered_queries if q.get("id") == str(filter_id).strip()]
        if not filtered_queries:
            print(f"[!] No query found with ID '{filter_id}'.")
            return {}

    if filter_category:
        filtered_queries = [q for q in filtered_queries if q.get("category") == str(filter_category).strip()]
        if not filtered_queries:
            print(f"[!] No query found under category '{filter_category}'.")
            return {}

    os.makedirs(results_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"run_{timestamp}.md"
    report_path = os.path.join(results_dir, report_filename)

    results = []
    pass_count = 0
    infra_count = 0
    review_count = 0
    fail_count = 0

    print(f"\n==========================================================================")
    print(f" MACHINEASSIST BENCHMARK TEST RUNNER")
    print(f" Target Endpoint: {endpoint}")
    print(f" Queries to run: {len(filtered_queries)}")
    print(f" Timestamp: {timestamp}")
    print(f"==========================================================================\n")

    for item in filtered_queries:
        qid = item.get("id", "?")
        query_text = item.get("query", "")
        category = item.get("category", "")
        expected_summary = item.get("expected_summary", "")

        req_payload = {
            "message": query_text,
            "session_id": f"bench_{qid}_{timestamp}"
        }

        status_code = 0
        elapsed_ms = 0.0
        data = None
        error_msg = None

        start_time = time.perf_counter()
        try:
            resp = requests.post(endpoint, json=req_payload, timeout=timeout)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            status_code = resp.status_code
            try:
                data = resp.json()
            except Exception:
                data = {"raw_text": resp.text}
        except requests.exceptions.ConnectionError:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            error_msg = f"Connection refused to {endpoint} (server not running)"
        except requests.exceptions.Timeout:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            error_msg = f"Request timed out after {timeout}s"
        except requests.exceptions.RequestException as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            error_msg = f"Request failed: {type(e).__name__} - {e}"

        status, actual_display = evaluate_response(item, status_code, data, error_msg)

        if status == "PASS":
            pass_count += 1
        elif status == "INFRASTRUCTURE_FAILURE":
            infra_count += 1
        elif status == "MANUAL_REVIEW":
            review_count += 1
        else:
            fail_count += 1

        results.append({
            "id": qid,
            "category": category,
            "query": query_text,
            "expected": expected_summary,
            "actual": actual_display,
            "status": status,
            "http_status": status_code,
            "time_ms": round(elapsed_ms, 1),
            "raw_response": data
        })

    # Output Console Table
    col_query = 42
    col_expected = 40
    col_actual = 50
    col_status = 22

    header = f"| {'Query':<{col_query}} | {'Expected':<{col_expected}} | {'Actual':<{col_actual}} | {'Status':<{col_status}} |"
    divider = f"|{'-' * (col_query + 2)}|{'-' * (col_expected + 2)}|{'-' * (col_actual + 2)}|{'-' * (col_status + 2)}|"

    print(header)
    print(divider)
    for r in results:
        q_disp = f'"{r["query"]}"'
        if len(q_disp) > col_query:
            q_disp = q_disp[:col_query - 3] + "..."

        e_disp = r["expected"]
        if len(e_disp) > col_expected:
            e_disp = e_disp[:col_expected - 3] + "..."

        # Replace newlines with spaces for single-line table display
        clean_actual = r["actual"].replace("\n", " ")
        if len(clean_actual) > col_actual:
            a_disp = clean_actual[:col_actual - 3] + "..."
        else:
            a_disp = clean_actual

        s_disp = r["status"]
        print(f"| {q_disp:<{col_query}} | {e_disp:<{col_expected}} | {a_disp:<{col_actual}} | {s_disp:<{col_status}} |")

    total = len(filtered_queries)
    summary_line = f"{pass_count}/{total} passed, {infra_count} infrastructure failures, {review_count} manual review needed."
    if fail_count > 0:
        summary_line += f" ({fail_count} failed)"

    print(f"\nSummary: {summary_line}")
    print(f"Results report saved to: {report_path}\n")

    # Generate Markdown Report File
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# MachineAssist Manual Test Runner Report\n\n")
        f.write(f"- **Timestamp:** `{timestamp}`\n")
        f.write(f"- **Endpoint:** `{endpoint}`\n")
        f.write(f"- **Queries Run:** {total}\n\n")
        f.write(f"| Query | Expected | Actual | Status |\n")
        f.write(f"|---|---|---|---|\n")
        for r in results:
            clean_q = r["query"].replace("|", "\\|")
            clean_exp = r["expected"].replace("|", "\\|")
            clean_act = r["actual"].replace("\n", " ").replace("|", "\\|")
            if len(clean_act) > 200:
                clean_act = clean_act[:197] + "..."
            f.write(f'| "{clean_q}" | {clean_exp} | {clean_act} | {r["status"]} |\n')

        f.write(f"\n{summary_line}\n\n")

        f.write(f"## Detailed Diagnostics\n\n")
        for r in results:
            f.write(f"### Query {r['id']} ({r['category']}): `{r['query']}`\n")
            f.write(f"- **Status:** `{r['status']}`\n")
            f.write(f"- **HTTP Status:** `{r['http_status']}` | **Latency:** `{r['time_ms']} ms`\n")
            f.write(f"- **Expected:** {r['expected']}\n")
            f.write(f"- **Actual:** {r['actual']}\n\n")

    return {
        "pass_count": pass_count,
        "infra_count": infra_count,
        "review_count": review_count,
        "fail_count": fail_count,
        "total": total,
        "report_path": report_path
    }


def main():
    parser = argparse.ArgumentParser(description="MachineAssist Benchmark Test Runner")
    parser.add_argument(
        "--endpoint",
        type=str,
        default=DEFAULT_ENDPOINT,
        help=f"Target API query endpoint (default: {DEFAULT_ENDPOINT})"
    )
    parser.add_argument(
        "--id",
        type=str,
        default=None,
        help="Run only a single query by ID (e.g. 1.1, 3.1)"
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="Run queries in a specific category (exact_code, natural_language, ambiguous, undocumented_gap)"
    )
    parser.add_argument(
        "--queries-file",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "test_queries.json"),
        help="Path to queries JSON file"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SEC,
        help="Request timeout in seconds"
    )

    args = parser.parse_args()

    queries_path = args.queries_file
    if not os.path.exists(queries_path):
        # Fallback to local tests/test_queries.json
        queries_path = "tests/test_queries.json"

    queries = load_queries(queries_path)

    run_tests(
        queries=queries,
        endpoint=args.endpoint,
        timeout=args.timeout,
        filter_id=args.id,
        filter_category=args.category
    )


if __name__ == "__main__":
    main()
