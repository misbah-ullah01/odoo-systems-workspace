# Repository Architecture

> **Navigation:** [Repository README](../README.md) · [ExcepTrack Module](../addons/exceptrack_security/README.md) · [ExcepTrack Technical Reference](modules/exceptrack.md)

## Overview

This is a **multi-module Odoo 19 monorepo**. All custom Odoo addons live under `addons/`, each as a fully self-contained module. Shared configuration and documentation live at the repository root.

---

## Directory Structure

```
odoo-systems-workspace/
│
├── addons/                            # All custom Odoo addon modules
│   └── exceptrack_security/           # Security Exception Lifecycle Management
│       ├── __manifest__.py            # Module metadata, version, dependencies, data files
│       ├── __init__.py                # Python package root; imports models/
│       ├── models/                    # ORM model classes (Python)
│       │   ├── __init__.py
│       │   ├── security_exception.py  # security.exception model
│       │   └── exception_control.py   # security.exception.control model
│       ├── views/                     # XML view definitions, form/list/kanban/menus
│       │   ├── security_exception_views.xml
│       │   ├── exception_control_views.xml
│       │   └── menus.xml
│       ├── security/                  # Groups, ACL CSV, record rules
│       │   ├── security_groups.xml
│       │   ├── ir.model.access.csv
│       │   └── security_rules.xml
│       ├── data/                      # Non-demo data: sequences, cron jobs
│       │   ├── sequence.xml
│       │   └── cron.xml
│       ├── demo/                      # Demo data loaded in --test or demo mode
│       │   └── demo.xml
│       ├── static/                    # Static assets (module icon, JS, CSS if any)
│       └── README.md                  # Module-level documentation
│
├── config/
│   └── odoo.conf.example              # Odoo server configuration reference
│
├── docs/
│   ├── architecture.md                # This file
│   └── modules/
│       └── exceptrack.md              # Full ExcepTrack data model & technical reference
│
├── .gitignore                         # Python/Odoo/IDE ignores
└── README.md                          # Repository overview & getting started guide
```

---

## Design Principles

| Principle                   | Rationale                                                                  |
|-----------------------------|----------------------------------------------------------------------------|
| **Module Isolation**        | Each addon is independently installable with no implicit coupling.         |
| **No Premature Abstraction**| Shared utilities are only extracted when two or more modules genuinely need them. |
| **Odoo-Native Conventions** | ORM, XML views, security groups, and record rules follow official Odoo 19 guidelines. |
| **No Cross-Module Deps**    | Cross-module dependencies must be declared in `__manifest__.py` and justified in documentation. |
| **Separation of Concerns**  | Server config (`config/`) is kept entirely separate from module logic (`addons/`). |
| **Audit-First Design**      | Any workflow module must integrate with `mail.thread` and `mail.activity.mixin` for traceability. |

---

## Module Anatomy

Every module in `addons/` follows this standard structure:

```
<module_name>/
├── __manifest__.py     # Required: name, version, category, depends, data[], license
├── __init__.py         # Required: imports models subpackage
├── models/
│   ├── __init__.py     # Required: imports each model file
│   └── *.py            # One file per logical model
├── views/
│   ├── *_views.xml     # Form, list, kanban views per model
│   └── menus.xml       # Menu items and actions
├── security/
│   ├── security_groups.xml       # res.groups definitions
│   ├── ir.model.access.csv       # CRUD ACL per group per model
│   └── security_rules.xml        # Record-level rules (optional)
├── data/
│   └── *.xml           # Sequences, email templates, cron jobs
├── demo/
│   └── demo.xml        # Sample records for demo mode
├── static/
│   └── description/
│       └── icon.png    # Module icon (256×256 PNG)
└── README.md           # Module overview (mirrored from manifest description)
```

### Data File Loading Order

Odoo loads files in the exact order listed under `'data'` in `__manifest__.py`. The required order is:

1. **Security** — Groups and ACLs must be loaded before any records that reference them.
2. **Data** — Sequences, cron jobs, and configuration records.
3. **Demo** — Sample data (loaded in demo/test mode only).
4. **Views** — Form, list, kanban, and menu definitions.

---

## Adding a New Module

1. Create the directory: `addons/<module_name>/`
2. Add `__manifest__.py` with at minimum: `name`, `version`, `category`, `depends`, `data`, and `license`.
3. Add `__init__.py` and a `models/` subpackage.
4. Create `security/ir.model.access.csv` for each model before adding views.
5. Register a module icon at `static/description/icon.png`.
6. Write a `README.md` in the module directory.
7. Add the module to the [Available Modules](../README.md#available-modules) table in the root `README.md`.
8. Create `docs/modules/<module_name>.md` with the full data model reference.

---

## Versioning Convention

Module versions follow the format: `<odoo_version>.<major>.<minor>.<patch>`

| Segment       | Meaning                                           |
|---------------|---------------------------------------------------|
| `19.0`        | Odoo major version this module targets            |
| `1`           | Major version (breaking changes)                  |
| `0`           | Minor version (new features, non-breaking)        |
| `0`           | Patch version (bug fixes)                         |

**Example:** `19.0.1.0.0` — first stable release for Odoo 19.

---

## Related Documents

| Document | Description |
|----------|-------------|
| [Repository README](../README.md) | Getting started, installation, deployment, and contributing |
| [ExcepTrack — Module README](../addons/exceptrack_security/README.md) | Features, usage, workflow states, and security groups |
| [ExcepTrack — Technical Reference](modules/exceptrack.md) | Full data model, state machine, validations, and integrations |
| [Odoo Config Example](../config/odoo.conf.example) | Annotated server configuration reference |
