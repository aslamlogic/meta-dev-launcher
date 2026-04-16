class SpecUpdater:

    def derive_constraints(self, findings):
        constraints = []

        for f in findings:
            constraints.append({
                "failure_code": f.get("failure_code"),
                "constraint": f.get("message"),
                "path": f.get("path")
            })

        return constraints
