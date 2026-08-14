# Odoo Custom Modules Monorepo

A multi-purpose repository for developing, testing, and deploying custom Odoo modules.

## Stack

| Component | Technology |
|-----------|------------|
| Platform  | Odoo 19 Community Edition |
| Backend   | Python 3.10+ |
| Frontend  | XML Views, OWL (when needed) |
| Database  | PostgreSQL (via Odoo ORM) |
| Hosting   | Skysize.io |

## Repository Structure

```
├── addons/                    # Custom Odoo modules
│   └── exceptrack_security/   # Security Exception Lifecycle Management
├── config/                    # Configuration examples
├── docs/                      # Documentation
│   └── modules/               # Per-module documentation
└── README.md
```

## Available Modules

| Module | Technical Name | Description | Status |
|--------|---------------|-------------|--------|
| ExcepTrack | `exceptrack_security` | Security Exception Lifecycle Management | In Development |

## Development Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/misbah-ullah01/odoo-systems-workspace.git
   ```

2. Add `addons/` to your Odoo `addons_path`:
   ```
   addons_path = /path/to/odoo/addons,/path/to/this/repo/addons
   ```

3. Restart Odoo and update the apps list.

4. Install the desired module from the Apps menu.

## Deployment

The modules are deployed to **Skysize.io**. See `config/odoo.conf.example` for configuration reference.

> **Important:** Never commit production credentials. Use environment variables for sensitive configuration.

## Contributing

- Each module is self-contained under `addons/<module_name>/`.
- Follow Odoo 19 conventions for models, views, and security.
- Keep modules independent — avoid unnecessary cross-module dependencies.
- Use descriptive commit messages: `feat(module): description`, `fix(module): description`.

## License

LGPL-3
