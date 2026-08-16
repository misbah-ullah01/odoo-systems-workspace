# ExcepTrack — Security Exception Lifecycle Management

> A custom Odoo 19 module for formally managing the complete lifecycle of temporary security exceptions within an organization.

[![Odoo](https://img.shields.io/badge/Odoo-19%20Community-714B67?logo=odoo&logoColor=white)](https://www.odoo.com/)
[![Version](https://img.shields.io/badge/Version-19.0.1.0.0-informational)](.)
[![License: LGPL-3](https://img.shields.io/badge/License-LGPL--3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Dependencies](#dependencies)
- [Installation](#installation)
- [Usage](#usage)
  - [Creating an Exception](#creating-an-exception)
  - [Workflow States](#workflow-states)
  - [Security Groups](#security-groups)
- [Technical Reference](#technical-reference)
- [Configuration](#configuration)
- [License](#license)
- [See Also](#see-also)

---

## Overview

When an organization cannot immediately remediate a security vulnerability or policy gap, a **security exception** is raised to formally document the accepted risk, apply compensating controls, and track the issue to resolution.

ExcepTrack provides a structured, auditable workflow for this process — from initial request through risk assessment, management approval, active monitoring, verification, and final closure — all within Odoo's native UI with full chatter history.

---

## Features

| Feature                   | Description                                                                    |
|---------------------------|--------------------------------------------------------------------------------|
| **Full Lifecycle**        | Multi-stage workflow: Draft → Assessment → Review → Approval → Active → Closure |
| **Risk Assessment**       | Tracks risk level (Low / Medium / High / Critical), likelihood, and impact     |
| **Compensating Controls** | Document and monitor temporary mitigating controls per exception               |
| **Role-Based Access**     | Four hierarchical security groups with implied inheritance                     |
| **Verification Workflow** | Pass/fail verification at closure with mandatory notes                         |
| **Exception Renewal**     | Extend expiring exceptions with a full audit trail                             |
| **Automated Reminders**   | Daily cron job flags exceptions expiring within the next 14 days               |
| **Chatter Integration**   | Full audit trail via Odoo's mail thread on every record                        |
| **Auto-References**       | Exceptions are assigned sequential references (`SEC-EXC/00001`)                |
| **Demo Data**             | Pre-loaded sample exceptions for evaluation and testing                        |

---

## Dependencies

| Module | Purpose                              |
|--------|--------------------------------------|
| `base` | Core Odoo framework                  |
| `mail` | Chatter, activities, notifications   |

---

## Installation

1. **Place the module** in your Odoo custom addons directory:

   ```bash
   cp -r exceptrack_security/ /path/to/odoo/custom/addons/
   ```

2. **Add the path** to `addons_path` in your `odoo.conf` (if not already included):

   ```ini
   addons_path = /opt/odoo/addons,/path/to/custom/addons
   ```

3. **Restart Odoo** and update the app list:

   Navigate to **Settings → Apps → Update Apps List**

4. **Search for "ExcepTrack"** and click **Install**.

---

## Usage

### Creating an Exception

1. Navigate to **ExcepTrack → Exceptions → All Exceptions**.
2. Click **New**.
3. Fill in:
   - **Title** — Short description of the exception.
   - **Description** — Detailed explanation of the security gap.
   - **Owner** — Who is accountable for the accepted risk.
   - **Risk Level** — Severity classification (Low / Medium / High / Critical).
   - **Business Justification** — Why the exception is necessary.
   - **Compensating Controls** — Any mitigations already in place.
4. Click **Submit for Assessment** to begin the workflow.

---

### Workflow States

```
Draft → Assessment → Review → Pending Approval → Active → Under Review
                       ↓              ↓                        ↓         ↓
                    Rejected       Rejected                 Renewed   Pending Verification
                                                                          ↓         ↓
                                                                       Closed    Active
                                                                       (Pass)    (Fail)
```

| State                 | Description                                              |
|-----------------------|----------------------------------------------------------|
| `Draft`               | Initial creation; not yet submitted                      |
| `Assessment`          | Risk assessment in progress                              |
| `Review`              | Security reviewer evaluating the exception               |
| `Pending Approval`    | Awaiting manager sign-off                                |
| `Active`              | Approved and actively monitored                          |
| `Under Review`        | Periodic review of an active exception                   |
| `Pending Verification`| Remediation verification in progress                     |
| `Closed`              | Verified and formally closed                             |
| `Rejected`            | Rejected during review or approval stage                 |

---

### Security Groups

Four hierarchical groups with implied inheritance:

```
Administrator
  └── Manager
        └── Reviewer
              └── User
```

| Group           | Permissions                                       |
|-----------------|---------------------------------------------------|
| **User**        | Create and manage own exceptions                  |
| **Reviewer**    | Review, assess, and verify exceptions             |
| **Manager**     | Approve or reject exceptions; see all records     |
| **Administrator** | Full configuration and system access            |

> Record rules further restrict visibility — users only see exceptions where they are the requester, owner, or reviewer. Managers and Administrators see all records.

---

## Technical Reference

### Module Info

| Property         | Value                                        |
|------------------|----------------------------------------------|
| Technical Name   | `exceptrack_security`                        |
| Version          | `19.0.1.0.0`                                 |
| Author           | Misbah Ullah                                 |
| License          | LGPL-3                                       |
| Odoo Compatibility | 19.0                                       |

### Models

**`security.exception`** — Core model representing a security exception request.

**`security.exception.control`** — Compensating controls linked to an exception.

### Key Technical Points

- **Reference Sequence:** Auto-generated as `SEC-EXC/00001`, `SEC-EXC/00002`, etc.
- **Cron Job:** Runs daily to flag exceptions where `expiration_date` is within 14 days.
- **Computed Fields:** `days_until_expiry` (Integer) and `is_expired` (Boolean) are computed server-side.
- **State Transitions:** Invalid transitions are blocked at the method level (not just the UI).
- **Validations:** Business justification, reviewer, approver, dates, and verification notes are all enforced before workflow progression.

For the full data model and field reference, see [`docs/modules/exceptrack.md`](../../docs/modules/exceptrack.md).

---

## Configuration

No additional configuration is required beyond installation. The module ships with:

- Default security groups and ACL rules (`security/`)
- An auto-incrementing reference sequence (`data/sequence.xml`)
- A daily scheduled action for expiry reminders (`data/cron.xml`)
- Optional demo data for quick evaluation (`demo/demo.xml`)

---

## License

This module is licensed under the **GNU Lesser General Public License v3.0 (LGPL-3)**.
See the [LGPL-3 license](https://www.gnu.org/licenses/lgpl-3.0.en.html) for full details.

---

## See Also

| Resource | Description |
|----------|-------------|
| [Full Technical Reference](../../docs/modules/exceptrack.md) | Complete data model, state machine diagram, validation rules, and integration points |
| [Repository Architecture](../../docs/architecture.md) | Monorepo structure, design principles, and module conventions |
| [Repository README](../../README.md) | Getting started, deployment, and contributing guide |
| [Odoo 19 Developer Docs](https://www.odoo.com/documentation/19.0/) | Official Odoo ORM, view, and security documentation |

---

*Part of the [Odoo Custom Modules Monorepo](../../README.md) — Maintained by [Misbah Ullah](https://github.com/misbah-ullah01)*
