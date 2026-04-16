import os
import textwrap

BASE = os.getcwd()

def write_file(path: str, content: str) -> None:
    full_path = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(content).lstrip("\n"))
    print(f"CREATED: {path}")

# =========================================================
# P6 VALIDATION SYSTEM — HARDENED COMPLEMENT
# =========================================================

write_file("iteration/failure_classifier.py", r'''
from typing import Dict, Any, List


class FailureClassifier:
    """
    Deterministic failure taxonomy for P6 validation.
    """

    TAXONOMY = {
        "SPEC_UNDERDETERMINED": "E-SPEC-UNDERDETERMINED",
        "SYNTAX": "E-SYNTAX",
        "DEPENDENCY": "E-DEPENDENCY",
        "STRUCTURE": "E-STRUCTURE",
        "BEHAVIOUR": "E-BEHAVIOUR",
        "SCHEMA": "E-SCHEMA",
        "GOVERNANCE": "E-GOVERNANCE",
        "SECURITY": "E-SECURITY",
        "LWP": "E-LWP",
        "UI": "E-UI",
        "RUNTIME": "E-RUNTIME",
        "UNKNOWN": "E-UNKNOWN",
    }

    def classify(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        classified = []
        for finding in findings:
            category = finding.get("category", "UNKNOWN")
            code = self.TAXONOMY.get(category, self.TAXONOMY["UNKNOWN"])
            enriched = dict(finding)
            enriched["failure_code"] = code
            classified.append(enriched)
        return classified
''')

write_file("iteration/dependency_validator.py", r'''
import importlib.util
import json
import os
from typing import Dict, Any, List


class DependencyValidator:
    """
    Checks basic Python and Node dependency presence without network installs.
    """

    def validate(self, workspace_path: str) -> Dict[str, Any]:
        findings: List[Dict[str, Any]] = []

        req_txt = os.path.join(workspace_path, "requirements.txt")
        if os.path.exists(req_txt):
            with open(req_txt, "r", encoding="utf-8") as f:
                packages = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
            for pkg in packages:
                module_name = pkg.split("==")[0].split(">=")[0].split("<=")[0].replace("-", "_")
                if importlib.util.find_spec(module_name) is None:
                    findings.append({
                        "category": "DEPENDENCY",
                        "message": f"Python dependency not importable: {pkg}",
                        "path": req_txt
                    })

        pkg_json = os.path.join(workspace_path, "package.json")
        if os.path.exists(pkg_json):
            try:
                with open(pkg_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                deps = {}
                deps.update(data.get("dependencies", {}))
                deps.update(data.get("devDependencies", {}))
                node_modules = os.path.join(workspace_path, "node_modules")
                if not os.path.isdir(node_modules):
                    findings.append({
                        "category": "DEPENDENCY",
                        "message": "package.json exists but node_modules directory is missing",
                        "path": pkg_json
                    })
                else:
                    for dep in deps.keys():
                        dep_path = os.path.join(node_modules, dep)
                        if not os.path.exists(dep_path):
                            findings.append({
                                "category": "DEPENDENCY",
                                "message": f"Node dependency missing from node_modules: {dep}",
                                "path": pkg_json
                            })
            except Exception as e:
                findings.append({
                    "category": "DEPENDENCY",
                    "message": f"package.json parse failure: {e}",
                    "path": pkg_json
                })

        return {
            "passed": len(findings) == 0,
            "findings": findings
        }
''')

write_file("iteration/structure_validator.py", r'''
import os
from typing import Dict, Any, List


class StructureValidator:
    """
    Validates required files and directory presence.
    """

    REQUIRED_ANY = [
        "meta_ui/api.py",
        "iteration/controller.py",
    ]

    def validate(self, workspace_path: str) -> Dict[str, Any]:
        findings: List[Dict[str, Any]] = []

        for rel_path in self.REQUIRED_ANY:
            full = os.path.join(workspace_path, rel_path)
            if not os.path.exists(full):
                findings.append({
                    "category": "STRUCTURE",
                    "message": f"Required file missing: {rel_path}",
                    "path": rel_path
                })

        apps_dir = os.path.join(workspace_path, "apps")
        if not os.path.isdir(apps_dir):
            findings.append({
                "category": "STRUCTURE",
                "message": "apps/ directory missing",
                "path": "apps/"
            })

        return {
            "passed": len(findings) == 0,
            "findings": findings
        }
''')

write_file("iteration/behaviour_validator.py", r'''
import importlib.util
import json
import os
import sys
from typing import Dict, Any, List

from fastapi.testclient import TestClient


class BehaviourValidator:
    """
    Validates runtime behaviour using FastAPI TestClient when app is present.
    """

    def _load_module_from_path(self, module_path: str):
        module_name = "_p6_runtime_target"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Unable to create import spec for {module_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    def validate(self, workspace_path: str) -> Dict[str, Any]:
        findings: List[Dict[str, Any]] = []
        api_path = os.path.join(workspace_path, "meta_ui", "api.py")

        if not os.path.exists(api_path):
            findings.append({
                "category": "BEHAVIOUR",
                "message": "Cannot run behaviour checks because meta_ui/api.py is missing",
                "path": "meta_ui/api.py"
            })
            return {"passed": False, "findings": findings}

        try:
            module = self._load_module_from_path(api_path)
            app = getattr(module, "app", None)
            if app is None:
                findings.append({
                    "category": "BEHAVIOUR",
                    "message": "FastAPI app object 'app' not found in meta_ui/api.py",
                    "path": "meta_ui/api.py"
                })
                return {"passed": False, "findings": findings}

            client = TestClient(app)

            response = client.get("/health")
            if response.status_code != 200:
                findings.append({
                    "category": "BEHAVIOUR",
                    "message": f"/health returned status {response.status_code}, expected 200",
                    "path": "/health"
                })
            else:
                try:
                    payload = response.json()
                    if payload.get("status") != "ok":
                        findings.append({
                            "category": "BEHAVIOUR",
                            "message": f"/health payload invalid: {json.dumps(payload)}",
                            "path": "/health"
                        })
                except Exception as e:
                    findings.append({
                        "category": "BEHAVIOUR",
                        "message": f"/health returned non-JSON payload: {e}",
                        "path": "/health"
                    })

        except Exception as e:
            findings.append({
                "category": "BEHAVIOUR",
                "message": f"Runtime validation failed: {e}",
                "path": "meta_ui/api.py"
            })

        return {
            "passed": len(findings) == 0,
            "findings": findings
        }
''')

write_file("iteration/governance_validator.py", r'''
import os
import re
from typing import Dict, Any, List


class GovernanceValidator:
    """
    Enforces no-markdown, no narrative contamination, deterministic textual restrictions.
    """

    PROHIBITED_PATTERNS = [
        r"```",
        r"\bAs we can see\b",
        r"\bIn this section\b",
        r"\bNext, we\b",
        r"\bHere is an explanation\b",
    ]

    ALLOWED_EXTENSIONS = {
        ".py", ".js", ".ts", ".tsx", ".json", ".yaml", ".yml", ".txt", ".md", ".toml", ".ini", ".cfg", ".sh"
    }

    def validate(self, workspace_path: str) -> Dict[str, Any]:
        findings: List[Dict[str, Any]] = []

        for root, _, files in os.walk(workspace_path):
            for file_name in files:
                ext = os.path.splitext(file_name)[1].lower()
                if ext not in self.ALLOWED_EXTENSIONS:
                    continue

                full_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(full_path, workspace_path)

                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        text = f.read()
                    for pattern in self.PROHIBITED_PATTERNS:
                        if re.search(pattern, text):
                            findings.append({
                                "category": "GOVERNANCE",
                                "message": f"Prohibited governance pattern found: {pattern}",
                                "path": rel_path
                            })
                except Exception as e:
                    findings.append({
                        "category": "GOVERNANCE",
                        "message": f"Unable to read file for governance validation: {e}",
                        "path": rel_path
                    })

        return {
            "passed": len(findings) == 0,
            "findings": findings
        }
''')

write_file("iteration/security_evaluator.py", r'''
import os
import re
from typing import Dict, Any, List


class SecurityEvaluator:
    """
    Simple static security scanner using deterministic blocklists.
    """

    BLOCKLIST = [
        r"\bsubprocess\b",
        r"\bos\.system\b",
        r"\beval\s*\(",
        r"\bexec\s*\(",
        r"\brequests\.",
        r"shell\s*=\s*True",
        r"OPENAI_API_KEY\s*=\s*[\"']",
        r"GITHUB_TOKEN\s*=\s*[\"']",
    ]

    FILE_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".json", ".sh"}

    def validate(self, workspace_path: str) -> Dict[str, Any]:
        findings: List[Dict[str, Any]] = []

        for root, _, files in os.walk(workspace_path):
            for file_name in files:
                ext = os.path.splitext(file_name)[1].lower()
                if ext not in self.FILE_EXTENSIONS:
                    continue

                full_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(full_path, workspace_path)

                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        text = f.read()
                    for pattern in self.BLOCKLIST:
                        if re.search(pattern, text):
                            findings.append({
                                "category": "SECURITY",
                                "message": f"Security blocklist pattern found: {pattern}",
                                "path": rel_path
                            })
                except Exception as e:
                    findings.append({
                        "category": "SECURITY",
                        "message": f"Unable to read file for security validation: {e}",
                        "path": rel_path
                    })

        return {
            "passed": len(findings) == 0,
            "findings": findings
        }
''')

write_file("iteration/lwp_validator.py", r'''
import os
from typing import Dict, Any, List


class LWPValidator:
    """
    Deterministic placeholder validator for locked workflow process presence.
    This checks artefact presence and obvious prohibited language.
    """

    PROHIBITED_TERMS = ["entitled", "liable", "will win", "prediction", "guaranteed outcome"]

    def validate(self, workspace_path: str) -> Dict[str, Any]:
        findings: List[Dict[str, Any]] = []

        rule_applicator = os.path.join(workspace_path, "iteration", "rule_applicator.py")
        if not os.path.exists(rule_applicator):
            findings.append({
                "category": "LWP",
                "message": "rule_applicator.py missing; deterministic LWP chain cannot be confirmed",
                "path": "iteration/rule_applicator.py"
            })

        for root, _, files in os.walk(workspace_path):
            for file_name in files:
                if not file_name.endswith((".py", ".txt", ".json", ".md")):
                    continue
                full_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(full_path, workspace_path)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        text = f.read().lower()
                    for term in self.PROHIBITED_TERMS:
                        if term in text:
                            findings.append({
                                "category": "LWP",
                                "message": f"Prohibited advisory/legal-outcome language found: {term}",
                                "path": rel_path
                            })
                except Exception:
                    pass

        return {
            "passed": len(findings) == 0,
            "findings": findings
        }
''')

write_file("iteration/ui_evaluator.py", r'''
import os
from typing import Dict, Any, List


class UIEvaluator:
    """
    Validates presence of required UI artefacts statically.
    """

    REQUIRED_UI_FILES = [
        "meta_ui/api.py"
    ]

    OPTIONAL_UI_MARKERS = [
        "spec_upload",
        "dashboard",
        "fault_panel",
        "deploy_panel"
    ]

    def validate(self, workspace_path: str) -> Dict[str, Any]:
        findings: List[Dict[str, Any]] = []

        for rel_path in self.REQUIRED_UI_FILES:
            full_path = os.path.join(workspace_path, rel_path)
            if not os.path.exists(full_path):
                findings.append({
                    "category": "UI",
                    "message": f"Required UI-related file missing: {rel_path}",
                    "path": rel_path
                })

        found_markers = set()
        for root, _, files in os.walk(workspace_path):
            for file_name in files:
                if file_name.endswith((".py", ".tsx", ".ts", ".js")):
                    full_path = os.path.join(root, file_name)
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            text = f.read().lower()
                        for marker in self.OPTIONAL_UI_MARKERS:
                            if marker in text:
                                found_markers.add(marker)
                    except Exception:
                        pass

        if len(found_markers) == 0:
            findings.append({
                "category": "UI",
                "message": "No expected UI markers found in codebase",
                "path": "workspace"
            })

        return {
            "passed": len(findings) == 0,
            "findings": findings
        }
''')

write_file("iteration/logging_service.py", r'''
import json
import os
from datetime import datetime
from typing import Dict, Any


class LoggingService:
    """
    JSONL logging service for deterministic run traces.
    """

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

    def _ts(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    def log(self, run_id: str, action: str, status: str, meta: Dict[str, Any] | None = None) -> str:
        path = os.path.join(self.log_dir, f"run_{run_id}.jsonl")
        entry = {
            "ts": self._ts(),
            "run_id": run_id,
            "action": action,
            "status": status,
            "meta": meta or {}
        }
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return path
''')

write_file("iteration/report_builder.py", r'''
import json
import os
from datetime import datetime
from typing import Dict, Any, List


class ReportBuilder:
    """
    Builds validation and audit reports.
    """

    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = reports_dir
        os.makedirs(self.reports_dir, exist_ok=True)

    def build_validation_report(self, run_id: str, passed: bool, findings: List[Dict[str, Any]]) -> str:
        report = {
            "run_id": run_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "passed": passed,
            "finding_count": len(findings),
            "findings": findings
        }
        path = os.path.join(self.reports_dir, f"validation_{run_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        return path

    def build_audit_report(self, run_id: str, summary: Dict[str, Any]) -> str:
        path = os.path.join(self.reports_dir, f"audit_{run_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        return path
''')

write_file("iteration/evaluator.py", r'''
import ast
import os
from typing import Dict, Any, List

from iteration.behaviour_validator import BehaviourValidator
from iteration.dependency_validator import DependencyValidator
from iteration.failure_classifier import FailureClassifier
from iteration.governance_validator import GovernanceValidator
from iteration.lwp_validator import LWPValidator
from iteration.report_builder import ReportBuilder
from iteration.security_evaluator import SecurityEvaluator
from iteration.structure_validator import StructureValidator
from iteration.ui_evaluator import UIEvaluator


class Evaluator:
    """
    Hardened P6 orchestrator.
    """

    def __init__(self):
        self.dependency_validator = DependencyValidator()
        self.structure_validator = StructureValidator()
        self.behaviour_validator = BehaviourValidator()
        self.governance_validator = GovernanceValidator()
        self.security_validator = SecurityEvaluator()
        self.lwp_validator = LWPValidator()
        self.ui_validator = UIEvaluator()
        self.failure_classifier = FailureClassifier()
        self.report_builder = ReportBuilder()

    def _syntax_validate_python(self, workspace_path: str) -> Dict[str, Any]:
        findings: List[Dict[str, Any]] = []
        for root, _, files in os.walk(workspace_path):
            for file_name in files:
                if file_name.endswith(".py"):
                    full_path = os.path.join(root, file_name)
                    rel_path = os.path.relpath(full_path, workspace_path)
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            source = f.read()
                        ast.parse(source)
                    except SyntaxError as e:
                        findings.append({
                            "category": "SYNTAX",
                            "message": f"Python syntax error: {e}",
                            "path": rel_path
                        })
                    except Exception as e:
                        findings.append({
                            "category": "SYNTAX",
                            "message": f"Python parse failure: {e}",
                            "path": rel_path
                        })
        return {
            "passed": len(findings) == 0,
            "findings": findings
        }

    def run(self, workspace_path: str, run_id: str = "default_run") -> Dict[str, Any]:
        results = []

        syntax_result = self._syntax_validate_python(workspace_path)
        results.append(syntax_result)

        dependency_result = self.dependency_validator.validate(workspace_path)
        results.append(dependency_result)

        structure_result = self.structure_validator.validate(workspace_path)
        results.append(structure_result)

        behaviour_result = self.behaviour_validator.validate(workspace_path)
        results.append(behaviour_result)

        governance_result = self.governance_validator.validate(workspace_path)
        results.append(governance_result)

        security_result = self.security_validator.validate(workspace_path)
        results.append(security_result)

        lwp_result = self.lwp_validator.validate(workspace_path)
        results.append(lwp_result)

        ui_result = self.ui_validator.validate(workspace_path)
        results.append(ui_result)

        all_findings: List[Dict[str, Any]] = []
        for result in results:
            all_findings.extend(result.get("findings", []))

        classified_findings = self.failure_classifier.classify(all_findings)
        passed = len(classified_findings) == 0

        report_path = self.report_builder.build_validation_report(
            run_id=run_id,
            passed=passed,
            findings=classified_findings
        )

        return {
            "passed": passed,
            "findings": classified_findings,
            "report_path": report_path
        }


def evaluate(workspace_path: str, run_id: str = "default_run") -> Dict[str, Any]:
    return Evaluator().run(workspace_path=workspace_path, run_id=run_id)
''')

print("P6 FULL COMPLEMENT WRITTEN")
