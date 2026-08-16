# Odoo Custom Modules Monorepo

> A production-ready monorepo for developing, testing, and deploying custom Odoo 19 modules — hosted on **Skysize.io**.

[![Odoo](https://img.shields.io/badge/Odoo-19%20Community-714B67?logo=odoo&logoColor=white)](https://www.odoo.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-ORM-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License: LGPL-3](https://img.shields.io/badge/License-LGPL--3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [Available Modules](#available-modules)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This monorepo houses custom Odoo 19 modules built for enterprise use. Each module is a fully self-contained Odoo addon placed under `addons/`, following Odoo 19 conventions for models, views, security, and lifecycle management.

Modules in this repo extend Odoo's core capabilities for security governance, compliance, and operational workflows.

---

## Tech Stack

| Layer       | Technology                        |
|-------------|-----------------------------------|
| Platform    | Odoo 19 Community Edition         |
| Backend     | Python 3.10+                      |
| Frontend    | XML Views, OWL (Odoo Web Library) |
| ORM / DB    | Odoo ORM over PostgreSQL          |
| Hosting     | Skysize.io                        |

---

## Repository Structure

```
odoo-systems-workspace/
│
├── addons/                            # Custom Odoo addon modules
│   └── exceptrack_security/           # Security Exception Lifecycle Management
│       ├── __manifest__.py            # Module metadata & data file declarations
│       ├── __init__.py
│       ├── models/                    # ORM model definitions
│       ├── views/                     # XML view definitions & menus
│       ├── security/                  # Groups, ACLs, record rules
│       ├── data/                      # Sequences, cron jobs
│       ├── demo/                      # Demo/sample data
│       ├── static/                    # Static assets (icons, JS, CSS)
│       └── README.md                  # Module-level documentation
│
├── config/
│   └── odoo.conf.example              # Configuration reference (never commit real credentials)
│
├── docs/
│   ├── architecture.md                # Repository architecture & design principles
│   └── modules/
│       └── exceptrack.md              # Detailed ExcepTrack module documentation
│
├── .gitignore
└── README.md                          # You are here
```

### 📚 Documentation

| Document | Description |
|----------|-------------|
| [Repository Architecture](docs/architecture.md) | Directory layout, design principles, module anatomy, versioning |
| [ExcepTrack — Module README](addons/exceptrack_security/README.md) | Features, installation, usage, and security groups |
| [ExcepTrack — Technical Reference](docs/modules/exceptrack.md) | Full data model, state machine, validations, integrations |
| [Odoo Config Example](config/odoo.conf.example) | Annotated server configuration reference |

---

## Available Modules


| Module | Technical Name | Version | Description | Docs | Status |
|--------|----------------|---------|-------------|------|--------|
| ExcepTrack | `exceptrack_security` | 19.0.1.0.0 | Security Exception Lifecycle Management | [README](addons/exceptrack_security/README.md) · [Reference](docs/modules/exceptrack.md) | 🟡 In Development |

---

## Getting Started

### Prerequisites

- **Odoo 19** Community or Enterprise installed and running
- **Python 3.10+**
- **PostgreSQL 14+**
- Git

### Installation

1. **Clone this repository** alongside your existing Odoo installation:

   ```bash
   git clone https://github.com/misbah-ullah01/odoo-systems-workspace.git
   ```

2. **Add the `addons/` path** to your Odoo configuration:

   ```ini
   # In your odoo.conf
   addons_path = /path/to/odoo/addons,/path/to/odoo-systems-workspace/addons
   ```

   See [`config/odoo.conf.example`](config/odoo.conf.example) for a full configuration reference.

3. **Restart the Odoo server:**

   ```bash
   sudo systemctl restart odoo
   # or
   ./odoo-bin -c /path/to/odoo.conf
   ```

4. **Update the app list** — Navigate to **Settings → Apps → Update Apps List**, then search for and install the desired module.

---

## Configuration

Copy the example configuration and customize it for your environment:

```bash
cp config/odoo.conf.example /etc/odoo/odoo.conf
```

> **⚠️ Security:** Never commit configuration files containing real credentials, database passwords, or admin master passwords. Use environment variables or a secrets manager in production.

---

## Deployment

Modules are deployed to **Skysize.io**. The general deployment flow is:

1. Push changes to the `main` branch.
2. Pull latest on the server and restart Odoo.
3. Apply model or view changes using the `-u` flag:

   ```bash
   ./odoo-bin -c /etc/odoo/odoo.conf -u exceptrack_security --stop-after-init
   ```

---

## Contributing

Contributions are welcome. Please follow these guidelines:

- **Module isolation** — Each module must be fully self-contained under `addons/<module_name>/`.
- **Odoo 19 conventions** — Follow standard patterns for models, views, and security.
- **No cross-module dependencies** — Unless genuinely required and clearly documented.
- **Commit message format:**

  ```
  feat(exceptrack_security): add renewal workflow
  fix(exceptrack_security): correct expiry date validation
  docs(exceptrack_security): update state machine diagram
  ```

- **New modules:** Add an entry to the [Available Modules](#available-modules) table and create documentation under `docs/modules/<module_name>.md`.

---

## License

This project is licensed under the **GNU Lesser General Public License v3.0 (LGPL-3)**.
See the [LGPL-3 license](https://www.gnu.org/licenses/lgpl-3.0.en.html) for full details.

---

*Maintained by [Misbah Ullah](https://github.com/misbah-ullah01)*
