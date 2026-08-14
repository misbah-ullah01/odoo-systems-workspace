{
    'name': 'ExcepTrack — Security Exception Management',
    'version': '19.0.1.0.0',
    'category': 'Security',
    'summary': 'Security Exception Lifecycle Management',
    'description': """
ExcepTrack — Security Exception Lifecycle Management
=====================================================

Manage the complete lifecycle of temporary security exceptions:

* **Create** — Document security exceptions with risk assessment
* **Review** — Assign reviewers for security evaluation
* **Approve** — Route through approval workflow
* **Monitor** — Track active exceptions with compensating controls
* **Verify** — Manual verification of remediation
* **Renew** — Extend exceptions when needed
* **Close** — Complete the lifecycle with verification records

Features:
---------
* Full lifecycle state machine (Draft → Active → Closed)
* Risk level tracking (Low / Medium / High / Critical)
* Compensating controls management
* Role-based access control (User / Reviewer / Manager / Admin)
* Expiration tracking with automated reminders
* Chatter integration for audit trail
* Demo data for quick evaluation
    """,
    'author': 'Misbah Ullah',
    'website': 'https://github.com/misbah-ullah01/odoo-systems-workspace',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
    ],
    'data': [
        # Security
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'security/security_rules.xml',
        # Data
        'data/sequence.xml',
        'data/cron.xml',
        # Views
        'views/security_exception_views.xml',
        'views/exception_control_views.xml',
        'views/menus.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
