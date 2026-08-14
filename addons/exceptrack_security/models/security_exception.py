from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, timedelta


class SecurityException(models.Model):
    _name = 'security.exception'
    _description = 'Security Exception'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'display_name'

    # -------------------------------------------------------------------------
    # SELECTION CONSTANTS
    # -------------------------------------------------------------------------
    STATES = [
        ('draft', 'Draft'),
        ('assessment', 'Assessment'),
        ('review', 'Review'),
        ('pending_approval', 'Pending Approval'),
        ('active', 'Active'),
        ('under_review', 'Under Review'),
        ('renewed', 'Renewed'),
        ('pending_verification', 'Pending Verification'),
        ('closed', 'Closed'),
        ('rejected', 'Rejected'),
    ]

    RISK_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    LIKELIHOOD_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    VERIFICATION_RESULTS = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ]

    # -------------------------------------------------------------------------
    # FIELDS — Identification
    # -------------------------------------------------------------------------
    reference = fields.Char(
        string='Reference',
        readonly=True,
        copy=False,
        default=lambda self: _('New'),
        tracking=True,
    )
    name = fields.Char(
        string='Title',
        required=True,
        tracking=True,
    )
    description = fields.Html(
        string='Description',
    )

    # -------------------------------------------------------------------------
    # FIELDS — Ownership
    # -------------------------------------------------------------------------
    requester_id = fields.Many2one(
        'res.users',
        string='Requester',
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
    )
    owner_id = fields.Many2one(
        'res.users',
        string='Owner',
        tracking=True,
    )
    reviewer_id = fields.Many2one(
        'res.users',
        string='Reviewer',
        tracking=True,
    )
    approver_id = fields.Many2one(
        'res.users',
        string='Approver',
        tracking=True,
    )

    # -------------------------------------------------------------------------
    # FIELDS — Risk
    # -------------------------------------------------------------------------
    risk_level = fields.Selection(
        selection=RISK_LEVELS,
        string='Risk Level',
        default='medium',
        required=True,
        tracking=True,
    )
    impact = fields.Text(
        string='Impact',
    )
    likelihood = fields.Selection(
        selection=LIKELIHOOD_LEVELS,
        string='Likelihood',
        default='medium',
    )
    risk_description = fields.Text(
        string='Risk Description',
    )

    # -------------------------------------------------------------------------
    # FIELDS — Justification
    # -------------------------------------------------------------------------
    business_justification = fields.Text(
        string='Business Justification',
    )
    technical_justification = fields.Text(
        string='Technical Justification',
    )

    # -------------------------------------------------------------------------
    # FIELDS — Dates
    # -------------------------------------------------------------------------
    start_date = fields.Date(
        string='Start Date',
        tracking=True,
    )
    review_date = fields.Date(
        string='Review Date',
        tracking=True,
    )
    expiration_date = fields.Date(
        string='Expiration Date',
        tracking=True,
    )

    # -------------------------------------------------------------------------
    # FIELDS — Lifecycle
    # -------------------------------------------------------------------------
    state = fields.Selection(
        selection=STATES,
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        copy=False,
    )

    # -------------------------------------------------------------------------
    # FIELDS — Compensating Controls
    # -------------------------------------------------------------------------
    control_ids = fields.One2many(
        'security.exception.control',
        'exception_id',
        string='Compensating Controls',
    )

    # -------------------------------------------------------------------------
    # FIELDS — Verification
    # -------------------------------------------------------------------------
    verification_result = fields.Selection(
        selection=VERIFICATION_RESULTS,
        string='Verification Result',
        tracking=True,
    )
    verified_by_id = fields.Many2one(
        'res.users',
        string='Verified By',
        tracking=True,
    )
    verification_date = fields.Date(
        string='Verification Date',
        tracking=True,
    )
    verification_notes = fields.Text(
        string='Verification Notes',
    )

    # -------------------------------------------------------------------------
    # FIELDS — Computed
    # -------------------------------------------------------------------------
    days_until_expiry = fields.Integer(
        string='Days Until Expiry',
        compute='_compute_days_until_expiry',
        store=True,
    )
    is_expired = fields.Boolean(
        string='Is Expired',
        compute='_compute_is_expired',
        store=True,
    )
    renewal_count = fields.Integer(
        string='Renewal Count',
        default=0,
        copy=False,
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
    )

    # -------------------------------------------------------------------------
    # COMPUTED METHODS
    # -------------------------------------------------------------------------
    @api.depends('expiration_date')
    def _compute_days_until_expiry(self):
        today = date.today()
        for record in self:
            if record.expiration_date:
                delta = record.expiration_date - today
                record.days_until_expiry = delta.days
            else:
                record.days_until_expiry = 0

    @api.depends('expiration_date', 'state')
    def _compute_is_expired(self):
        today = date.today()
        for record in self:
            if record.expiration_date and record.state in ('active', 'under_review'):
                record.is_expired = record.expiration_date < today
            else:
                record.is_expired = False

    @api.depends('reference', 'name')
    def _compute_display_name(self):
        for record in self:
            if record.reference and record.reference != _('New'):
                record.display_name = f"[{record.reference}] {record.name or ''}"
            else:
                record.display_name = record.name or ''

    # -------------------------------------------------------------------------
    # CONSTRAINTS
    # -------------------------------------------------------------------------
    @api.constrains('start_date', 'expiration_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.expiration_date:
                if record.expiration_date < record.start_date:
                    raise ValidationError(
                        _("Expiration date cannot be before the start date.")
                    )

    @api.constrains('review_date', 'expiration_date')
    def _check_review_before_expiry(self):
        for record in self:
            if record.review_date and record.expiration_date:
                if record.review_date > record.expiration_date:
                    raise ValidationError(
                        _("Review date cannot be after the expiration date.")
                    )

    # -------------------------------------------------------------------------
    # CRUD OVERRIDES
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', _('New')) == _('New'):
                vals['reference'] = self.env['ir.sequence'].next_by_code(
                    'security.exception.sequence'
                ) or _('New')
        return super().create(vals_list)

    # -------------------------------------------------------------------------
    # WORKFLOW ACTIONS
    # -------------------------------------------------------------------------
    def action_submit(self):
        """Draft → Assessment"""
        self.ensure_one()
        if not self.business_justification:
            raise UserError(
                _("Business justification is required before submitting.")
            )
        self.write({'state': 'assessment'})

    def action_assess(self):
        """Assessment → Review"""
        self.ensure_one()
        if not self.reviewer_id:
            raise UserError(
                _("A reviewer must be assigned before moving to review.")
            )
        if not self.risk_level:
            raise UserError(
                _("Risk level must be set before assessment is complete.")
            )
        self.write({'state': 'review'})

    def action_recommend_approval(self):
        """Review → Pending Approval"""
        self.ensure_one()
        if not self.approver_id:
            raise UserError(
                _("An approver must be assigned before recommending approval.")
            )
        self.write({'state': 'pending_approval'})

    def action_approve(self):
        """Pending Approval → Active"""
        self.ensure_one()
        if not self.start_date:
            raise UserError(
                _("Start date is required before activation.")
            )
        if not self.expiration_date:
            raise UserError(
                _("Expiration date is required before activation.")
            )
        self.write({'state': 'active'})

    def action_reject(self):
        """Review / Pending Approval → Rejected"""
        self.ensure_one()
        if self.state not in ('review', 'pending_approval'):
            raise UserError(
                _("Rejection is only possible during Review or Pending Approval.")
            )
        self.write({'state': 'rejected'})

    def action_revise(self):
        """Rejected → Draft (allow revision)"""
        self.ensure_one()
        if self.state != 'rejected':
            raise UserError(
                _("Only rejected exceptions can be revised.")
            )
        self.write({'state': 'draft'})

    def action_initiate_review(self):
        """Active → Under Review"""
        self.ensure_one()
        self.write({'state': 'under_review'})

    def action_renew(self):
        """Under Review → Renewed → Active"""
        self.ensure_one()
        if self.state != 'under_review':
            raise UserError(
                _("Only exceptions under review can be renewed.")
            )
        self.write({
            'state': 'active',
            'renewal_count': self.renewal_count + 1,
        })
        self.message_post(
            body=_("Exception renewed (renewal #%d).") % self.renewal_count,
            message_type='comment',
            subtype_xmlid='mail.mt_note',
        )

    def action_request_verification(self):
        """Under Review → Pending Verification"""
        self.ensure_one()
        if self.state != 'under_review':
            raise UserError(
                _("Verification can only be requested for exceptions under review.")
            )
        self.write({
            'state': 'pending_verification',
            'verification_result': False,
            'verified_by_id': False,
            'verification_date': False,
            'verification_notes': False,
        })

    def action_verify_pass(self):
        """Pending Verification → Closed (pass)"""
        self.ensure_one()
        if self.state != 'pending_verification':
            raise UserError(
                _("Verification is only possible for exceptions pending verification.")
            )
        if not self.verification_notes:
            raise UserError(
                _("Verification notes are required before closing.")
            )
        self.write({
            'state': 'closed',
            'verification_result': 'pass',
            'verified_by_id': self.env.user.id,
            'verification_date': date.today(),
        })

    def action_verify_fail(self):
        """Pending Verification → Active (fail)"""
        self.ensure_one()
        if self.state != 'pending_verification':
            raise UserError(
                _("Verification is only possible for exceptions pending verification.")
            )
        if not self.verification_notes:
            raise UserError(
                _("Verification notes are required.")
            )
        self.write({
            'state': 'active',
            'verification_result': 'fail',
            'verified_by_id': self.env.user.id,
            'verification_date': date.today(),
        })

    # -------------------------------------------------------------------------
    # SCHEDULED ACTIONS
    # -------------------------------------------------------------------------
    @api.model
    def _cron_check_expiring_exceptions(self):
        """Identify exceptions expiring within 14 days and create activities."""
        threshold = date.today() + timedelta(days=14)
        expiring = self.search([
            ('state', 'in', ['active', 'under_review']),
            ('expiration_date', '<=', threshold),
            ('expiration_date', '>=', date.today()),
        ])
        activity_type = self.env.ref('mail.mail_activity_data_warning', raise_if_not_found=False)
        for record in expiring:
            existing = self.env['mail.activity'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', record.id),
                ('activity_type_id', '=', activity_type.id if activity_type else False),
                ('summary', 'like', 'Exception Expiring'),
            ], limit=1)
            if not existing:
                record.activity_schedule(
                    'mail.mail_activity_data_warning',
                    date_deadline=record.expiration_date,
                    summary=_("Exception Expiring Soon"),
                    note=_(
                        "Security exception '%s' expires on %s. "
                        "Please review and take action."
                    ) % (record.name, record.expiration_date),
                    user_id=(record.owner_id or record.requester_id).id,
                )
