# AcroCorp Cloud Engine Troubleshooting & Incident Response

## Error Codes & Resolution

### ERR-401: Authentication Token Expired or Invalid
- **Symptom**: HTTP 401 Unauthorized returned on API requests.
- **Cause**: The provided Bearer token has passed its 90-day validity window or was revoked by an administrator.
- **Resolution**: Generate a new Bearer token in the AcroCorp Admin Portal under IAM Settings > Service Accounts. Update the `Authorization` header in your client application.

### ERR-429: Rate Limit Exceeded
- **Symptom**: HTTP 429 Too Many Requests response code.
- **Cause**: The incoming request rate exceeded the tier limit (e.g. 1,000 req/min for Free Tier, 10,000 req/min for Pro Tier).
- **Resolution**: Implement exponential backoff with jitter in client requests, or request a quota upgrade to Pro/Enterprise Tier via Customer Support.

### ERR-503: Cluster Capacity Exceeded
- **Symptom**: HTTP 503 Service Unavailable during peak compute workloads.
- **Cause**: All execution pods in the assigned regional worker pool are fully utilized.
- **Resolution**: Enable multi-region routing in your workspace settings to allow workload distribution to secondary regions (`eu-central-1` or `ap-southeast-1`).

## Incident SLA & Response Times
AcroCorp Technical Support categorizes incidents into three priority levels:
- **P1 Critical**: Production system offline or major data corruption. SLA initial response time is 15 minutes (24/7 coverage).
- **P2 Major**: Significant performance degradation or loss of high-priority feature. SLA initial response time is 1 hour (Business Hours).
- **P3 Minor**: General inquiries, minor bug reports, or documentation issues. SLA initial response time is 24 business hours.
