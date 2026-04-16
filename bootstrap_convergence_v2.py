import os
import subprocess
from textwrap import dedent


def write_file(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.rstrip() + "\n")
    print(f"UPDATED: {path}")


LLM_INTERFACE = dedent(
    '''
    import json
    import os
    from typing import Any, Dict, List

    from openai import OpenAI


    def _get_client() -> OpenAI:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        return OpenAI(api_key=api_key)


    def _build_system_message() -> str:
        return """
    You are a deterministic code repair engine.

    HARD RULES:
    1. Modify only the files listed in allowed_files.
    2. Do not invent new architecture.
    3. Do not add markdown fences.
    4. Return only raw source code for the target file.
    5. Prioritise the repair_contract over all other context.
    6. Preserve unrelated working logic.
    7. If the target is a FastAPI app, keep the code runnable.
    """


    def _build_user_message(
        spec_text: str,
        repair_contract: List[Dict[str, Any]],
        allowed_files: List[str],
        target_file: str,
    ) -> str:
        contract_json = json.dumps(repair_contract, indent=2, ensure_ascii=False)
        allowed_files_json = json.dumps(allowed_files, indent=2, ensure_ascii=False)

        return f"""
    BASE_SPEC:
    {spec_text}

    TARGET_FILE:
    {target_file}

    ALLOWED_FILES:
    {allowed_files_json}

    REPAIR_CONTRACT:
    {contract_json}

    OUTPUT_REQUIREMENT:
    Return only the full raw source code for {target_file}.
    """


    def generate(
        spec_text: str,
        repair_contract: List[Dict[str, Any]],
        allowed_files: List[str],
        target_file: str = "generated_app/main.py",
    ) -> str:
        client = _get_client()

        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0,
            messages=[
                {"role": "system", "content": _build_system_message()},
                {
                    "role": "user",
                    "content": _build_user_message(
                        spec_text=spec_text,
                        repair_contract=repair_contract,
                        allowed_files=allowed_files,
                        target_file=target_file,
                    ),
                },
            ],
        )

        content = response.choices[0].message.content
        if not content or not isinstance(content, str):
            raise RuntimeError("LLM returned empty content")

        cleaned = content.strip()

        if cleaned.startswith("```") and cleaned.endswith("```"):
            cleaned = cleaned.strip("`").strip()
            if cleaned.startswith("python"):
                cleaned = cleaned[len("python"):].lstrip()

        return cleaned
    '''
)

SPEC_UPDATER = dedent(
    '''
    from typing import Any, Dict, List


    class SpecUpdater:
        """
        Converts validation findings into bounded deterministic repair objects.
        """

        FAILURE_TO_ACTION = {
            "E-SYNTAX": "fix_syntax",
            "E-DEPENDENCY": "fix_dependency",
            "E-STRUCTURE": "fix_structure",
            "E-BEHAVIOUR": "fix_behaviour",
            "E-SCHEMA": "fix_schema",
            "E-GOVERNANCE": "fix_governance",
            "E-SECURITY": "fix_security",
            "E-LWP": "fix_lwp",
            "E-UI": "fix_ui",
            "E-SPEC-UNDERDETERMINED": "preserve_scope",
            "E-UNKNOWN": "fix_conservatively",
        }

        FAILURE_TO_GUIDANCE = {
            "E-SYNTAX": "Correct syntax exactly where flagged without rewriting unrelated logic.",
            "E-DEPENDENCY": "Resolve imports or declarations without introducing undeclared dependencies.",
            "E-STRUCTURE": "Restore the required file, symbol, route, or object structure.",
            "E-BEHAVIOUR": "Correct runtime behaviour to satisfy the required endpoint contract.",
            "E-SCHEMA": "Correct schema mismatch without weakening validation.",
            "E-GOVERNANCE": "Remove prohibited patterns and preserve deterministic behaviour.",
            "E-SECURITY": "Remove insecure patterns and replace them conservatively.",
            "E-LWP": "Remove prohibited legal/advisory language and preserve allowed wording.",
            "E-UI": "Restore required UI artefacts only where explicitly required.",
            "E-SPEC-UNDERDETERMINED": "Do not invent missing features; stay within explicit scope.",
            "E-UNKNOWN": "Apply the smallest safe correction to the flagged issue.",
        }

        def derive_constraints(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            repair_contract: List[Dict[str, Any]] = []

            for finding in findings:
                failure_code = finding.get("failure_code", "E-UNKNOWN")
                message = str(finding.get("message", "")).strip()
                path = str(finding.get("path", "generated_app/main.py")).strip() or "generated_app/main.py"

                repair_contract.append(
                    {
                        "failure_code": failure_code,
                        "path": path,
                        "action": self.FAILURE_TO_ACTION.get(failure_code, "fix_conservatively"),
                        "guidance": self.FAILURE_TO_GUIDANCE.get(
                            failure_code,
                            self.FAILURE_TO_GUIDANCE["E-UNKNOWN"],
                        ),
                        "message": message,
                        "forbidden_regressions": [
                            "Do not change files outside the allowed scope.",
                            "Do not remove an existing FastAPI app object if present.",
                            "Do not remove an existing /health endpoint if already correct.",
                            "Do not add commentary, markdown, or explanations into source code.",
                        ],
                        "validation_target": failure_code,
                    }
                )

            return repair_contract
    '''
)

CONTROLLER = dedent(
    '''
    import os
    from typing import Any, Dict, List, Set

    from engine.llm_interface import generate
    from iteration.evaluator import evaluate
    from iteration.spec_updater import SpecUpdater


    class IterationController:
        def __init__(self, max_iterations: int = 5):
            self.max_iterations = max_iterations
            self.spec_updater = SpecUpdater()

        def _target_file(self, workspace_path: str) -> str:
            return os.path.join(workspace_path, "generated_app", "main.py")

        def _write_output(self, path: str, content: str) -> None:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

        def _score(self, result: Dict[str, Any]) -> int:
            findings = result.get("findings", []) or []
            passed = bool(result.get("passed", False))
            base = 10 if passed else 0
            return base - len(findings)

        def _failure_signature(self, result: Dict[str, Any]) -> Set[str]:
            findings = result.get("findings", []) or []
            signature: Set[str] = set()
            for finding in findings:
                code = str(finding.get("failure_code", "E-UNKNOWN"))
                path = str(finding.get("path", ""))
                message = str(finding.get("message", ""))
                signature.add(f"{code}|{path}|{message}")
            return signature

        def run(self, workspace_path: str, initial_spec_text: str, run_id: str = "run") -> Dict[str, Any]:
            target_path = self._target_file(workspace_path)
            allowed_files: List[str] = ["generated_app/main.py"]

            previous_score = None
            previous_signature: Set[str] = set()
            repair_contract: List[Dict[str, Any]] = []

            for iteration_index in range(self.max_iterations):
                print(f"ITERATION {iteration_index}")

                generated_code = generate(
                    spec_text=initial_spec_text,
                    repair_contract=repair_contract,
                    allowed_files=allowed_files,
                    target_file="generated_app/main.py",
                )

                self._write_output(target_path, generated_code)

                result = evaluate(generated_code)
                score = self._score(result)
                print(f"Score: {score}")

                if result.get("passed", False):
                    print("VALIDATED_BUILD")
                    return {
                        "status": "SUCCESS",
                        "score": score,
                        "iteration": iteration_index,
                        "result": result,
                    }

                current_signature = self._failure_signature(result)

                if previous_score is not None and score <= previous_score:
                    print("NO IMPROVEMENT -> STOP")
                    return {
                        "status": "FAIL",
                        "reason": "no_improvement",
                        "score": score,
                        "iteration": iteration_index,
                        "result": result,
                    }

                if previous_signature and current_signature == previous_signature:
                    print("IDENTICAL FAILURE SIGNATURE -> STOP")
                    return {
                        "status": "FAIL",
                        "reason": "identical_failure_signature",
                        "score": score,
                        "iteration": iteration_index,
                        "result": result,
                    }

                findings = result.get("findings", []) or []
                repair_contract = self.spec_updater.derive_constraints(findings)

                previous_score = score
                previous_signature = current_signature

            return {
                "status": "FAIL",
                "reason": "max_iterations_reached",
                "iteration": self.max_iterations,
            }
    '''
)

RUN_AUTONOMY_TEST = dedent(
    '''
    from dotenv import load_dotenv
    load_dotenv()

    from iteration.controller import IterationController


    def main():
        controller = IterationController(max_iterations=3)

        spec = """
    Build a FastAPI app:
    - GET /health
    - return {"status": "ok"}
    """

        result = controller.run(
            workspace_path=".",
            initial_spec_text=spec,
            run_id="autonomy_test"
        )

        print("FINAL RESULT:", result)


    if __name__ == "__main__":
        main()
    '''
)


write_file("engine/llm_interface.py", LLM_INTERFACE)
write_file("iteration/spec_updater.py", SPEC_UPDATER)
write_file("iteration/controller.py", CONTROLLER)
write_file("run_autonomy_test.py", RUN_AUTONOMY_TEST)

subprocess.run(["git", "add", "engine/llm_interface.py", "iteration/spec_updater.py", "iteration/controller.py", "run_autonomy_test.py", "bootstrap_convergence_v2.py"], check=True)
subprocess.run(["git", "commit", "-m", "Upgrade to convergence v2"], check=True)
subprocess.run(["git", "push"], check=True)

print("CONVERGENCE V2 DEPLOYED")
