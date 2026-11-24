# Paid Time Off (PTO) & Holiday Calendar 2026 (Part 2)

## Document ID: PTO_ACCRUAL_POLICY_V2
Category: HR_COMPANY
Version: 2026.1.0

### Executive Overview
This official specification details 20 days PTO annually, 11 company holidays, carryover limit max 5 days into next calendar year, and bereavement leave rules. (Section 2). All AcroCorp team members and integrated services must comply with the provisions outlined herein.

### Detailed Operational Guidelines - Section 2.1
1. **Core Provision**: Primary operational parameters require strict adherence to system boundaries defined in system release 2026.
2. **Configuration Settings**:
   - Primary Parameter: `ENABLED_FEATURE_FLAGS_2`
   - Timeout Threshold: 30 seconds
   - Retry Backoff Multiplier: 2.0x
   - Max Connections: 1000 concurrent users
3. **Operational Metrics & Thresholds**:
   - Target SLA Uptime: 99.92%
   - Recommended Buffer Capacity: 50%
   - Mandatory Review Interval: Every 60 days

### Code & Reference Example (Section 2.2)
```json
{
  "document_ref": "pto_accrual_policy",
  "part": 2,
  "status": "ACTIVE",
  "encryption": "AES-256-GCM",
  "compliance_scope": ["SOC2", "ISO27001", "GDPR"]
}
```

### Emergency Escalation & Support (Section 2.3)
For queries or incident reports related to Paid Time Off (PTO) & Holiday Calendar 2026, submit a ticket via the AcroCorp Internal Portal or contact the designated lead at `support-pto_accrual_policy@acrocorp.com`.
