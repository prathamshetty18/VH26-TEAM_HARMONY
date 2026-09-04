# Demo Queries & Expected Behaviors

## Demo 1: Exact Error Code
- **Query:** "What does E101 mean on CNC-100?"
- **Expected Result:** Machine-specific troubleshooting answer for CNC-100's E101 (Motor overheating).

## Demo 2: Natural Language Symptom
- **Query:** "Why is my Press-200 machine stopping due to oil pressure?"
- **Expected Result:** Semantic retrieval identifies Press-200 E101 (Low hydraulic pressure) and returns troubleshooting steps.

## Demo 3: Cross-Manual Ambiguity
- **Query:** "What does error code E101 mean?"
- **Expected Result:** System identifies E101 in multiple manuals (CNC-100 and Press-200) and asks for clarification (`ambiguous: true`).

## Demo 4: Insufficient Information
- **Query:** "How do I replace the spindle bearing on CNC-100?"
- **Expected Result:** System recognizes that this topic is not covered in the manuals and refuses to answer without hallucinating.
