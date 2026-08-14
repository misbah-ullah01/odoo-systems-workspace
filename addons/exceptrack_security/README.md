# ExcepTrack — Security Exception Lifecycle Management

## Overview

ExcepTrack is a custom Odoo module for managing the complete lifecycle of temporary security exceptions within an organization.

## Features

- **Full Lifecycle Management** — Draft → Assessment → Review → Approval → Active → Verification → Closure
- **Risk Assessment** — Track risk levels (Low/Medium/High/Critical), impact, and likelihood
- **Compensating Controls** — Document and track temporary controls that reduce risk
- **Role-Based Access** — User, Reviewer, Manager, and Administrator security groups
- **Verification Workflow** — Manual verification with pass/fail outcomes
- **Exception Renewal** — Extend exceptions with full audit trail
- **Automated Reminders** — Daily cron job flags exceptions expiring within 14 days
- **Chatter Integration** — Full audit trail via Odoo mail thread

## Dependencies

| Module | Purpose |
|--------|---------|
| `base` | Core Odoo framework |
| `mail` | Chatter, activities, notifications |

## Installation

1. Place this module in your Odoo custom addons directory.
2. Update the apps list: Settings → Apps → Update Apps List.
3. Search for "ExcepTrack" and click Install.

## Usage

### Creating an Exception

1. Navigate to **ExcepTrack → Exceptions → All Exceptions**.
2. Click **Create**.
3. Fill in the title, description, ownership, and risk assessment.
4. Add a business justification.
5. Click **Submit** to begin the workflow.

### Workflow States

| State | Description |
|-------|-------------|
| Draft | Initial creation, not yet submitted |
| Assessment | Risk assessment in progress |
| Review | Security reviewer evaluating the exception |
| Pending Approval | Awaiting manager approval |
| Active | Approved and being monitored |
| Under Review | Periodic review of active exception |
| Pending Verification | Remediation verification in progress |
| Closed | Verified and closed |
| Rejected | Rejected during review or approval |

### Security Groups

| Group | Permissions |
|-------|------------|
| User | Create and manage own exceptions |
| Reviewer | Review and verify exceptions |
| Manager | Approve or reject exceptions |
| Administrator | Full configuration access |

## Technical Details

- **Models**: `security.exception`, `security.exception.control`
- **Sequence**: `SEC-EXC/00001` auto-generated references
- **Cron**: Daily check for expiring exceptions (14-day window)

## License

LGPL-3
