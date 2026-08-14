from odoo import models, fields


class ExceptionControl(models.Model):
    _name = 'security.exception.control'
    _description = 'Security Exception Compensating Control'
    _order = 'sequence, id'

    # -------------------------------------------------------------------------
    # SELECTION CONSTANTS
    # -------------------------------------------------------------------------
    CONTROL_TYPES = [
        ('network', 'Network Restriction'),
        ('monitoring', 'Additional Monitoring'),
        ('logging', 'Additional Logging'),
        ('access', 'Access Restriction'),
        ('manual', 'Manual Review'),
        ('segmentation', 'Network Segmentation'),
        ('other', 'Other'),
    ]

    CONTROL_STATUSES = [
        ('planned', 'Planned'),
        ('implemented', 'Implemented'),
        ('verified', 'Verified'),
    ]

    # -------------------------------------------------------------------------
    # FIELDS
    # -------------------------------------------------------------------------
    exception_id = fields.Many2one(
        'security.exception',
        string='Security Exception',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    name = fields.Char(
        string='Control Name',
        required=True,
    )
    description = fields.Text(
        string='Description',
    )
    control_type = fields.Selection(
        selection=CONTROL_TYPES,
        string='Control Type',
        required=True,
        default='other',
    )
    status = fields.Selection(
        selection=CONTROL_STATUSES,
        string='Status',
        default='planned',
        required=True,
    )
    responsible_id = fields.Many2one(
        'res.users',
        string='Responsible',
    )
    implementation_date = fields.Date(
        string='Implementation Date',
    )
    notes = fields.Text(
        string='Notes',
    )
