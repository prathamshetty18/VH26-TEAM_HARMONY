import re

class SessionMemory:
    """
    In-memory Python store per session_id holding recent conversation context.
    """
    def __init__(self):
        self.sessions = {}

    def get_session(self, session_id):
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "last_machine": None,
                "last_error_code": None,
                "last_answer": None
            }
        return self.sessions[session_id]

    def update_session(self, session_id, machine=None, error_code=None, last_answer=None):
        sess = self.get_session(session_id)
        if machine:
            sess["last_machine"] = machine
        if error_code:
            sess["last_error_code"] = error_code
        if last_answer:
            sess["last_answer"] = last_answer

    def resolve_query_with_memory(self, session_id, query):
        """
        If query contains vague pronouns e.g. "that", "it", "this" and lacks machine/error_code,
        or if query is a machine-selection follow-up (e.g. "Press-200" / "CNC-100") lacking error code,
        inject stored memory context.
        """
        sess = self.get_session(session_id)
        last_m = sess.get("last_machine")
        last_e = sess.get("last_error_code")

        vague_terms = ["that", "it", "this", "what if", "how about"]
        query_lower = query.lower().strip()
        
        is_vague = any(term in query_lower for term in vague_terms)

        # Check if query is selecting a machine while an error code is active in memory
        from src.query_understanding import parse_query
        pq = parse_query(query)
        is_machine_selection = pq.get("machine") is not None and pq.get("error_code") is None and bool(last_e)

        augmented_query = query
        if is_vague or is_machine_selection:
            injections = []
            if last_m and last_m.lower() not in query_lower and not is_machine_selection:
                injections.append(f"machine {last_m}")
            if last_e and last_e.lower() not in query_lower:
                injections.append(f"error code {last_e}")

            if injections:
                augmented_query = f"{query} (regarding {' '.join(injections)})"

        return augmented_query

memory_store = SessionMemory()
