{
    "status": "failure",
    "failing_endpoints": ["POST /echo"],
    "schema_mismatches": [
        {
            "method": "GET",
            "path": "/health",
            "expected_response": {"status": "string"},
            "actual_response": {"ok": True}
        }
    ],
    "post_failures": [
        {
            "method": "POST",
            "path": "/echo",
            "reason": "missing request schema"
        }
    ]
}
