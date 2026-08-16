# ExcepTrack — Technical Reference

> Detailed data model, state machine, validation rules, and security reference for the `exceptrack_security` Odoo module.

> **Navigation:** [Repository README](../../README.md) · [Module README](../../addons/exceptrack_security/README.md) · [Repository Architecture](../architecture.md)

---

## Table of Contents

- [Purpose](#purpose)
- [Use Cases](#use-cases)
- [Data Model](#data-model)
  - [security.exception](#securityexception)
  - [security.exception.control](#securityexceptioncontrol)
- [State Machine](#state-machine)
- [Server-Side Validations](#server-side-validations)
- [Security Architecture](#security-architecture)
- [Automated Actions](#automated-actions)
- [Integration Points](#integration-points)

---

## Purpose

ExcepTrack manages the **lifecycle of temporary security exceptions**. When an organization cannot immediately remediate a security issue, it creates a security exception to formally document the accepted risk, apply compensating controls, track expiry, and verify resolution.

This module provides a structured, auditable process for this — from initial request through risk assessment, management approval, active monitoring, verification, and final closure.

---

## Use Cases

- Legacy systems requiring outdated protocols (TLS 1.0, SSH v1)
- Unpatched systems awaiting vendor certification
- Shared service accounts pending migration to individual accounts
- Temporary network access during facility changes or migrations
- Unsupported operating systems in OT/SCADA environments
- Third-party software with known vulnerabilities awaiting replacement

---

## Data Model

### security.exception

The core model representing a security exception request and its full lifecycle.

#### Identification

| Field       | Type           | Description                              |
|-------------|----------------|------------------------------------------|
| `reference` | `Char`         | Auto-generated sequential ID (`SEC-EXC/00001`); read-only |
| `name`      | `Char`         | Short title of the exception             |
| `description` | `Html`       | Rich-text detailed description of the security gap |

#### Ownership & Assignment

| Field          | Type                 | Description                           |
|----------------|----------------------|---------------------------------------|
| `requester_id` | `Many2one(res.users)` | User who created the exception request |
| `owner_id`     | `Many2one(res.users)` | User accountable for the accepted risk |
| `reviewer_id`  | `Many2one(res.users)` | Assigned security reviewer             |
| `approver_id`  | `Many2one(res.users)` | Assigned approving manager             |

#### Risk Assessment

| Field                  | Type        | Values / Description                           |
|------------------------|-------------|------------------------------------------------|
| `risk_level`           | `Selection` | `low` / `medium` / `high` / `critical`         |
| `likelihood`           | `Selection` | `low` / `medium` / `high`                      |
| `impact`               | `Text`      | Description of potential impact if exploited   |
| `risk_description`     | `Text`      | Narrative risk analysis                        |
| `business_justification` | `Text`    | Business reason for accepting the exception    |
| `technical_justification` | `Text`   | Technical reason why immediate fix isn't feasible |

#### Dates & Lifecycle

| Field             | Type   | Description                                     |
|-------------------|--------|-------------------------------------------------|
| `start_date`      | `Date` | Date the exception becomes effective            |
| `review_date`     | `Date` | Date of next scheduled periodic review         |
| `expiration_date` | `Date` | Date the exception expires                      |

#### State

| Field   | Type        | Values                                                                                    |
|---------|-------------|-------------------------------------------------------------------------------------------|
| `state` | `Selection` | `draft` / `assessment` / `review` / `pending_approval` / `active` / `under_review` / `pending_verification` / `closed` / `rejected` |

#### Compensating Controls

| Field        | Type      | Description                                      |
|--------------|-----------|--------------------------------------------------|
| `control_ids` | `One2many` | Linked `security.exception.control` records     |

#### Verification

| Field                 | Type                  | Description                              |
|-----------------------|-----------------------|------------------------------------------|
| `verification_result` | `Selection`           | `pass` / `fail`                          |
| `verified_by_id`      | `Many2one(res.users)` | User who performed verification          |
| `verification_date`   | `Date`                | Date verification was completed          |
| `verification_notes`  | `Text`                | Findings and evidence from verification  |

#### Computed Fields

| Field              | Type      | Description                                    |
|--------------------|-----------|------------------------------------------------|
| `days_until_expiry` | `Integer` | Computed: days remaining until `expiration_date` |
| `is_expired`        | `Boolean` | Computed: `True` if today > `expiration_date`  |
| `renewal_count`     | `Integer` | Number of times the exception has been renewed |

---

### security.exception.control

Compensating controls linked to a security exception. A single exception may have multiple controls.

| Field                 | Type                  | Description                                               |
|-----------------------|-----------------------|-----------------------------------------------------------|
| `exception_id`        | `Many2one(security.exception)` | Parent exception record                        |
| `name`                | `Char`                | Name / title of the compensating control                  |
| `description`         | `Text`                | What the control does and how it mitigates risk           |
| `control_type`        | `Selection`           | `network` / `monitoring` / `logging` / `access` / `manual` / `segmentation` / `other` |
| `status`              | `Selection`           | `planned` / `implemented` / `verified`                    |
| `responsible_id`      | `Many2one(res.users)` | Person responsible for implementing/maintaining the control |
| `implementation_date` | `Date`                | Date the control was or will be implemented               |
| `notes`               | `Text`                | Additional context or implementation notes                |

---

## State Machine

```
                              ┌──────────────┐
                              │    Draft     │ ◄─────────────────────────┐
                              └──────┬───────┘                           │
                                     │ submit                            │ reset to draft
                                     ▼                                   │
                              ┌──────────────┐                      ┌────┴──────┐
                              │  Assessment  │                      │  Rejected │
                              └──────┬───────┘                      └───────────┘
                                     │ complete assessment                ▲
                                     ▼                                   │ reject
                              ┌──────────────┐                           │
                              │    Review    │ ──────────────────────────┘
                              └──────┬───────┘
                                     │ recommend approval                ▲
                                     ▼                                   │ reject
                              ┌──────────────────┐                      │
                              │ Pending Approval │ ─────────────────────┘
                              └────────┬─────────┘
                                       │ approve
                                       ▼
                              ┌──────────────┐
                        ┌────►│    Active    │◄──────────────┐
                        │     └──────┬───────┘               │
                        │            │ trigger review         │ fail verification
                        │            ▼                        │
                        │     ┌──────────────┐               │
                   renew│     │ Under Review │               │
                        │     └──────┬───────┘               │
                        └────────────┤                        │
                                     │ request verification   │
                                     ▼                        │
                              ┌─────────────────────┐        │
                              │ Pending Verification │────────┘
                              └──────────┬──────────┘
                                         │ pass verification
                                         ▼
                              ┌──────────────┐
                              │    Closed    │
                              └──────────────┘
```

### Transition Summary

| From                | Action                     | To                    |
|---------------------|----------------------------|-----------------------|
| `draft`             | Submit                     | `assessment`          |
| `assessment`        | Complete assessment         | `review`              |
| `assessment`        | Reject                     | `rejected`            |
| `review`            | Recommend approval         | `pending_approval`    |
| `review`            | Reject                     | `rejected`            |
| `pending_approval`  | Approve                    | `active`              |
| `pending_approval`  | Reject                     | `rejected`            |
| `rejected`          | Reset to Draft             | `draft`               |
| `active`            | Trigger Review             | `under_review`        |
| `under_review`      | Renew                      | `active`              |
| `under_review`      | Request Verification       | `pending_verification` |
| `pending_verification` | Pass Verification       | `closed`              |
| `pending_verification` | Fail Verification       | `active`              |

---

## Server-Side Validations

The following validations are enforced at the Python method level (not just the UI) and will raise `UserError` if violated:

| Trigger                       | Validation                                                     |
|-------------------------------|----------------------------------------------------------------|
| Submit for Assessment         | `business_justification` must be non-empty                     |
| Complete Assessment           | `reviewer_id` must be assigned                                 |
| Recommend Approval            | `approver_id` must be assigned                                 |
| Activate (Approve)            | `start_date` and `expiration_date` must be set                 |
| Activate (Approve)            | `expiration_date` ≥ `start_date`                               |
| Activate (Approve)            | If set, `review_date` ≤ `expiration_date`                      |
| Close (Pass/Fail Verification)| `verification_notes` must be non-empty                         |
| Any state transition          | Invalid transition paths are blocked at the method level       |

---

## Security Architecture

Four hierarchical groups with implied inheritance (each group inherits permissions of all groups below it):

```
exceptrack_security.group_security_admin
  └── exceptrack_security.group_security_manager
        └── exceptrack_security.group_security_reviewer
              └── exceptrack_security.group_security_user
```

### Record-Level Visibility (Record Rules)

| Group       | Record Rule                                                                         |
|-------------|--------------------------------------------------------------------------------------|
| User        | Can only see records where they are `requester_id` OR `owner_id` OR `reviewer_id`   |
| Reviewer    | Inherits User rules + full visibility of records they are assigned to review         |
| Manager     | Sees **all** records regardless of ownership or assignment                           |
| Admin       | Sees **all** records regardless of ownership or assignment                           |

---

## Automated Actions

### Expiry Reminder Cron (`data/cron.xml`)

| Property   | Value                                    |
|------------|------------------------------------------|
| Name       | ExcepTrack: Check Expiring Exceptions    |
| Frequency  | Daily                                    |
| Action     | Flags exceptions where `expiration_date` is within the next **14 days** |
| Behavior   | Adds an activity or log note on matching records to alert the owner      |

---

## Integration Points

| Integration               | Details                                                               |
|---------------------------|-----------------------------------------------------------------------|
| `mail.thread`             | All `security.exception` records have a full chatter thread          |
| `mail.activity.mixin`     | Supports scheduled activities (reminders, to-dos) on exceptions      |
| `ir.sequence`             | Auto-generates `SEC-EXC/XXXXX` references via `data/sequence.xml`    |
| `ir.cron`                 | Daily job checks expiry windows via `data/cron.xml`                  |
| Odoo UI                   | Integrated via native form, list, kanban, and search views           |

---

## Related Documents

| Document | Description |
|----------|-------------|
| [Module README](../../addons/exceptrack_security/README.md) | Features, installation, usage, workflow states, and security groups |
| [Repository README](../../README.md) | Getting started, deployment, and contributing |
| [Repository Architecture](../architecture.md) | Monorepo structure, design principles, versioning convention |
| [Odoo 19 Developer Docs](https://www.odoo.com/documentation/19.0/) | Official Odoo ORM, view, and security documentation |
