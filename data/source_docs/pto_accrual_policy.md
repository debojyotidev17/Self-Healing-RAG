# Paid Time Off (PTO) & Holiday Calendar 2026 (Part 1)

## Document ID: PTO_ACCRUAL_POLICY_V1
Category: HR_COMPANY
Version: 2026.1.0

### Executive Overview
This official specification details 20 days PTO annually, 11 company holidays, carryover limit max 5 days into next calendar year, and bereavement leave rules. (Section 1). All AcroCorp team members and integrated services must comply with the provisions outlined herein.

### Detailed Operational Guidelines - Section 1.1
1. **Core Provision**: Primary operational parameters require strict adherence to system boundaries defined in system release 2026.
2. **Configuration Settings**:
   - Primary Parameter: `ENABLED_FEATURE_FLAGS_1`
   - Timeout Threshold: 15 seconds
   - Retry Backoff Multiplier: 2.0x
   - Max Connections: 500 concurrent users
3. **Operational Metrics & Thresholds**:
   - Target SLA Uptime: 99.91%
   - Recommended Buffer Capacity: 25%
   - Mandatory Review Interval: Every 30 days

### Code & Reference Example (Section 1.2)
```json
{
  "document_ref": "pto_accrual_policy",
  "part": 1,
  "status": "ACTIVE",
  "encryption": "AES-256-GCM",
  "compliance_scope": ["SOC2", "ISO27001", "GDPR"]
}
```

### Emergency Escalation & Support (Section 1.3)
For queries or incident reports related to Paid Time Off (PTO) & Holiday Calendar 2026, submit a ticket via the AcroCorp Internal Portal or contact the designated lead at `support-pto_accrual_policy@acrocorp.com`.
