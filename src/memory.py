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

    def update_session(self, session_id, machine=None, error_code=None, last_answer=None, clear_machine=False):
        sess = self.get_session(session_id)
        if clear_machine:
            sess["last_machine"] = None
        elif machine:
            sess["last_machine"] = machine
        if error_code:
            sess["last_error_code"] = error_code
        if last_answer:
            sess["last_answer"] = last_answer

    def resolve_query_with_memory(self, session_id, query):
        """
        Seamlessly connects multi-turn dialogue with active session context:
        1. Context Continuation: Vague follow-ups or queries lacking machine/error inherit active session state.
        2. Machine Switch: A user specifying a machine while an error code is active inherits the error code.
        3. Error Switch: A user specifying an error code while a machine is active inherits the machine,
           unless it's a standalone definition query testing cross-manual ambiguity.
        """
        sess = self.get_session(session_id)
        last_m = sess.get("last_machine")
        last_e = sess.get("last_error_code")

        # If session has no prior context, nothing to augment
        if not last_m and not last_e:
            return query

        from src.query_understanding import parse_query
        pq = parse_query(query)
        has_new_machine = pq.get("machine") is not None
        has_new_error = pq.get("error_code") is not None

        query_lower = query.lower().strip()
        injections = []

        # Case 1: Machine specified, error code missing -> inherit error code
        if has_new_machine and not has_new_error and last_e:
            if last_e.lower() not in query_lower:
                injections.append(f"error code {last_e}")

        # Case 2: Error specified, machine missing -> inherit machine ONLY if not a standalone definition query
        elif has_new_error and not has_new_machine and last_m:
            is_definition_query = bool(re.search(r"^(what\s+does|meaning\s+of|what\s+is|\bdefinition\b|\bexplain\b)?\s*(error\s+code\s+|fault\s+|error\s+)?([a-z]-?\d{3,4}|sym-[a-z0-9-]+)\s*(mean|\?|$)", query_lower))
            if not is_definition_query and last_m.lower() not in query_lower:
                injections.append(f"machine {last_m}")

        # Case 3: Neither machine nor error specified in follow-up -> inherit both only if follow-up intent
        elif not has_new_machine and not has_new_error:
            # Diagnostic target terms indicating follow-up on previous error
            diagnostic_intent_words = {
                "step", "steps", "procedure", "cause", "causes", "meaning", "mean",
                "fix", "fixes", "remedy", "solution", "action", "corrective",
                "inspect", "inspection", "check", "detail", "details", "explain",
                "troubleshoot", "troubleshooting", "resolve", "resolution"
            }
            # Pronouns referring to prior subject (only if accompanied by question or action verb)
            context_pronouns = {"this", "that", "it"}

            from src.safety import FACTORY_DOMAIN_VOCAB
            query_tokens = set(re.findall(r"\b[a-zA-Z0-9_-]+\b", query_lower))

            has_diagnostic_intent = bool(query_tokens.intersection(diagnostic_intent_words))
            has_domain_vocab = bool(query_tokens.intersection(FACTORY_DOMAIN_VOCAB))
            has_pronoun_reference = bool(query_tokens.intersection(context_pronouns)) and any(
                w in query_tokens for w in {"why", "how", "what", "fix", "do", "explain", "about"}
            )

            # Common off-topic triggers that should never inherit industrial equipment context
            off_topic_words = {
                "weather", "president", "cake", "bake", "recipe", "joke", "poem",
                "flower", "flowers", "movie", "song", "capital", "country", "football",
                "soccer", "game", "who", "when", "birthday", "dinner", "lunch", "pizza",
                "led", "blinking", "blinks", "flashing", "flicker", "flickering", "beep", "beeps"
            }
            is_off_topic = bool(query_tokens.intersection(off_topic_words))

            # Must have real follow-up intent and must not be an off-topic query
            if is_off_topic or not (has_diagnostic_intent or has_domain_vocab or has_pronoun_reference):
                return query

            if last_m and last_m.lower() not in query_lower:
                injections.append(f"machine {last_m}")
            if last_e and last_e.lower() not in query_lower:
                injections.append(f"error code {last_e}")

        if injections:
            return f"{query} (regarding {' '.join(injections)})"

        return query

memory_store = SessionMemory()
