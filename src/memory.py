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
            if sess.get("last_machine") and sess.get("last_machine") != machine:
                # Reset error code when switching to a different machine
                sess["last_error_code"] = None
            sess["last_machine"] = machine
        if error_code:
            sess["last_error_code"] = error_code
        elif machine and not error_code:
            # Query was for general machine without error code
            sess["last_error_code"] = None
        if last_answer:
            sess["last_answer"] = last_answer

    def resolve_query_with_memory(self, session_id, query):
        """
        Seamlessly connects multi-turn dialogue with active session context:
        1. Context Continuation: Vague follow-ups or queries lacking machine/error inherit active session state.
        2. Machine Switch: A user specifying a machine while an error code is active inherits the error code.
        3. Error Switch: A user specifying an error code while a machine is active inherits the machine.
        """
        sess = self.get_session(session_id)
        last_m = sess.get("last_machine")
        last_e = sess.get("last_error_code")

        # If session has no prior context, nothing to augment
        if not last_m and not last_e:
            return query

        from src.query_understanding import parse_query
        pq = parse_query(query)
        new_machine = pq.get("machine")
        has_new_machine = new_machine is not None
        has_new_error = pq.get("error_code") is not None

        query_lower = query.lower().strip()
        injections = []

        is_diagram_or_overview = bool(re.search(
            r"\b(diagram|diagrams|schematic|schematics|image|images|drawing|drawings|blueprint|blueprints|circuit|circuits|flowchart|layout|overview|manual|guide|spec|specs)\b",
            query_lower
        ))

        # If user explicitly asks for a diagram or overview, do NOT inject an old error code
        if is_diagram_or_overview:
            if not has_new_machine and last_m:
                injections.append(f"machine {last_m}")
            if injections:
                return f"{query} (regarding {' '.join(injections)})"
            return query

        # If machine changed, do NOT carry over error code from a different machine
        if has_new_machine and last_m and new_machine != last_m:
            return query

        # Case 1: Machine specified, error code missing -> inherit error code
        if has_new_machine and not has_new_error and last_e:
            if last_e.lower() not in query_lower:
                injections.append(f"error code {last_e}")

        # Case 2: Error specified, machine missing -> inherit machine
        elif has_new_error and not has_new_machine and last_m:
            if last_m.lower() not in query_lower:
                injections.append(f"machine {last_m}")

        # Case 3: Neither machine nor error specified in follow-up -> inherit both only if follow-up intent
        elif not has_new_machine and not has_new_error:
            is_followup = bool(re.search(
                r"\b(it|that|again|fix|troubleshoot|step|steps|cause|causes|action|actions|procedure|how|why|explain|solve|resolve|clear|reset|do|should|first|second|third|next|check|now|mean)\b",
                query_lower
            ))
            if is_followup:
                if last_m and last_m.lower() not in query_lower:
                    injections.append(f"machine {last_m}")
                if last_e and last_e.lower() not in query_lower:
                    injections.append(f"error code {last_e}")

        if injections:
            return f"{query} (regarding {' '.join(injections)})"

        return query

memory_store = SessionMemory()
