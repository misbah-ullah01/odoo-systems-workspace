# Repository Architecture

## Overview

This is a multi-purpose Odoo 19 custom modules monorepo. Each module is a self-contained Odoo addon under the `addons/` directory.

## Structure

```
odoo-systems-workspace/
│
├── README.md                          # Repository overview
├── .gitignore                         # Python/Odoo ignores
│
├── addons/                            # Custom Odoo modules
│   ├── exceptrack_security/           # Security Exception Management
│   │   ├── __manifest__.py
│   │   ├── __init__.py
│   │   ├── models/
│   │   ├── views/
│   │   ├── security/
│   │   ├── data/
│   │   ├── demo/
│   │   ├── static/
│   │   └── README.md
│   │
│   └── [future modules...]
│
├── config/                            # Configuration examples
│   └── odoo.conf.example
│
└── docs/                              # Documentation
    ├── architecture.md                # This file
    └── modules/
        └── exceptrack.md              # ExcepTrack module docs
```

## Design Principles

1. **Module Isolation** — Each module is independent and self-contained.
2. **No Premature Abstraction** — Shared code only when genuinely needed.
3. **Standard Odoo Conventions** — Follow Odoo 19 ORM, views, and security patterns.
4. **No Cross-Module Dependencies** — Unless genuinely required.
5. **Separation of Concerns** — Deployment config separate from module logic.

## Adding a New Module

1. Create `addons/<module_name>/` with `__init__.py` and `__manifest__.py`.
2. Add `models/`, `views/`, `security/` directories as needed.
3. Declare dependencies only on modules you genuinely use.
4. Add module documentation to `docs/modules/<module_name>.md`.
5. Update the root `README.md` module table.
