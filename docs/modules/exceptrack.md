# ExcepTrack — Module Documentation

## Purpose

ExcepTrack manages the lifecycle of temporary security exceptions. When an organization cannot immediately remediate a security issue, it creates a security exception to formally document, track, and eventually resolve the accepted risk.

## Use Cases

- Legacy systems requiring outdated protocols (TLS 1.0, SSH v1)
- Unpatched systems awaiting vendor certification
- Shared service accounts pending migration
- Temporary network access during facility changes
- Unsupported operating systems in OT/SCADA environments

## Data Model

### security.exception

The core model representing a security exception request.

| Field | Type | Description |
|-------|------|-------------|
| reference | Char | Auto-generated (SEC-EXC/00001) |
| name | Char | Exception title |
| description | Html | Detailed description |
| requester_id | Many2one (res.users) | Who requested the exception |
| owner_id | Many2one (res.users) | Who owns the risk |
| reviewer_id | Many2one (res.users) | Assigned security reviewer |
| approver_id | Many2one (res.users) | Assigned approver |
| risk_level | Selection | Low / Medium / High / Critical |
| likelihood | Selection | Low / Medium / High |
| impact | Text | Impact description |
| risk_description | Text | Risk narrative |
| business_justification | Text | Business reason for the exception |
| technical_justification | Text | Technical reason for the exception |
| start_date | Date | When the exception begins |
| review_date | Date | When periodic review is due |
| expiration_date | Date | When the exception expires |
| state | Selection | Current lifecycle state |
| control_ids | One2many | Compensating controls |
| verification_result | Selection | Pass / Fail |
| verified_by_id | Many2one (res.users) | Who performed verification |
| verification_date | Date | When verification occurred |
| verification_notes | Text | Verification findings |
| days_until_expiry | Integer (computed) | Days remaining |
| is_expired | Boolean (computed) | Whether past expiration |
| renewal_count | Integer | Number of renewals |

### security.exception.control

Compensating controls linked to an exception.

| Field | Type | Description |
|-------|------|-------------|
| exception_id | Many2one | Parent exception |
| name | Char | Control name |
| description | Text | Control description |
| control_type | Selection | network / monitoring / logging / access / manual / segmentation / other |
| status | Selection | planned / implemented / verified |
| responsible_id | Many2one (res.users) | Person responsible |
| implementation_date | Date | When implemented |
| notes | Text | Additional notes |

## State Machine

```
Draft → Assessment → Review → Pending Approval → Active → Under Review
                       ↓              ↓                        ↓      ↓
                    Rejected       Rejected                Renewed   Pending Verification
                       ↓                                     ↓           ↓         ↓
                     Draft                                Active      Closed     Active
                   (Revise)                                          (Pass)     (Fail)
```

## Server-Side Validations

- Business justification required before submission
- Reviewer required before assessment completion
- Approver required before recommending approval
- Start date and expiration date required before activation
- Expiration date must be ≥ start date
- Review date must be ≤ expiration date
- Verification notes required before pass/fail
- Invalid state transitions blocked at the method level

## Security

Four hierarchical groups with implied inheritance:

```
Administrator
  └── Manager
       └── Reviewer
            └── User
```

Record rules restrict visibility based on the user's relationship to the exception (requester, owner, reviewer). Managers and Admins see all records.
