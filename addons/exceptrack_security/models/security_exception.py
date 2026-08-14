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
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk'),
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
    # HELPER METHODS — Robust Group User Lookup & Dynamic Domains
    # -------------------------------------------------------------------------
    def _get_group_users(self, xml_id):
        """Safely fetch all users belonging to a security group across any Odoo ORM version."""
        group = self.env.ref(xml_id, raise_if_not_found=False)
        if not group:
            return self.env['res.users']
        
        try:
            if hasattr(group, 'user_ids') and group.user_ids:
                return group.user_ids
        except Exception:
            pass

        try:
            if hasattr(group, 'users') and group.users:
                return group.users
        except Exception:
            pass

        User = self.env['res.users']
        if 'groups_id' in User._fields:
            return User.search([('groups_id', 'in', [group.id])])
        if 'group_ids' in User._fields:
            return User.search([('group_ids', 'in', [group.id])])
        
        return User

    def _default_start_date(self):
        return date.today()

    def _default_review_date(self):
        return date.today() + timedelta(days=30)

    def _default_expiration_date(self):
        return date.today() + timedelta(days=90)

    # -------------------------------------------------------------------------
    # FIELDS — Identification
    # -------------------------------------------------------------------------
    reference = fields.Char(
        string='Reference ID',
        readonly=True,
        copy=False,
        default=lambda self: _('New'),
        tracking=True,
        help="Unique reference number generated automatically (e.g. SEC-EXC/00001).",
    )
    name = fields.Char(
        string='Exception Title',
        required=True,
        tracking=True,
        help="Brief title describing the security exception (e.g. Legacy TLS 1.0 Server).",
    )
    description = fields.Html(
        string='Detailed Summary',
        help="Provide a full description of the system, vulnerability, or issue requiring an exception.",
    )
    color = fields.Integer(
        string='Color Index',
        compute='_compute_color',
        store=True,
    )

    # -------------------------------------------------------------------------
    # FIELDS — Ownership & Assignments (Filtered Dropdowns)
    # -------------------------------------------------------------------------
    requester_id = fields.Many2one(
        'res.users',
        string='Requested By',
        default=lambda self: self.env.user,
        required=True,
        readonly=True,
        tracking=True,
        help="The person submitting this exception request (automatically assigned).",
    )
    owner_id = fields.Many2one(
        'res.users',
        string='Risk Owner',
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
        help="The person accountable for managing this risk and implementing controls.",
    )
    reviewer_id = fields.Many2one(
        'res.users',
        string='Security Reviewer',
        domain="[('share', '=', False)]",
        tracking=True,
        help="The security engineer assigned to evaluate this request (Filtered to Reviewers only).",
    )
    approver_id = fields.Many2one(
        'res.users',
        string='Approving Manager',
        domain="[('share', '=', False)]",
        tracking=True,
        help="The manager authorized to officially approve or reject this exception (Filtered to Managers only).",
    )

    # -------------------------------------------------------------------------
    # FIELDS — Risk Ranking
    # -------------------------------------------------------------------------
    risk_level = fields.Selection(
        selection=RISK_LEVELS,
        string='Risk Severity',
        default='medium',
        required=True,
        tracking=True,
        help="Rank the severity of this risk: Low, Medium, High, or Critical.",
    )
    impact = fields.Text(
        string='Business Impact',
        help="What happens if this vulnerability or exception is exploited?",
    )
    likelihood = fields.Selection(
        selection=LIKELIHOOD_LEVELS,
        string='Exploit Likelihood',
        default='medium',
        help="How likely is an exploit to occur? (Low, Medium, High).",
    )
    risk_description = fields.Text(
        string='Risk Details',
        help="Technical notes on CVSS scores, vulnerability vectors, or CVE IDs.",
    )

    # -------------------------------------------------------------------------
    # FIELDS — Justification
    # -------------------------------------------------------------------------
    business_justification = fields.Text(
        string='Business Justification',
        help="Why is this exception necessary? (e.g. Vendor delay, critical business continuity).",
    )
    technical_justification = fields.Text(
        string='Technical Justification',
        help="What technical constraints prevent immediate remediation?",
    )

    # -------------------------------------------------------------------------
    # FIELDS — Dates & Deadlines
    # -------------------------------------------------------------------------
    start_date = fields.Date(
        string='Effective Start Date',
        default=_default_start_date,
        required=True,
        tracking=True,
        help="Date when this security exception becomes effective.",
    )
    review_date = fields.Date(
        string='Scheduled Review Date',
        default=_default_review_date,
        required=True,
        tracking=True,
        help="Date when the security team must conduct a periodic review.",
    )
    expiration_date = fields.Date(
        string='Expiration Deadline',
        default=_default_expiration_date,
        required=True,
        tracking=True,
        help="Final date when this exception expires and must be closed or renewed.",
    )

    # -------------------------------------------------------------------------
    # FIELDS — Lifecycle State
    # -------------------------------------------------------------------------
    state = fields.Selection(
        selection=STATES,
        string='Lifecycle Stage',
        default='draft',
        required=True,
        tracking=True,
        copy=False,
    )

    # -------------------------------------------------------------------------
    # FIELDS — Compensating Controls & Verification
    # -------------------------------------------------------------------------
    control_ids = fields.One2many(
        'security.exception.control',
        'exception_id',
        string='Compensating Controls',
        help="Temporary security controls put in place to mitigate the risk.",
    )
    verification_result = fields.Selection(
        selection=VERIFICATION_RESULTS,
        string='Verification Outcome',
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
        string='Verification Findings',
        help="Detailed notes confirming remediation has been verified.",
    )

    # -------------------------------------------------------------------------
    # FIELDS — Computed Indicators
    # -------------------------------------------------------------------------
    days_until_expiry = fields.Integer(
        string='Days Remaining',
        compute='_compute_days_until_expiry',
        store=True,
    )
    is_expired = fields.Boolean(
        string='Expired Indicator',
        compute='_compute_is_expired',
        store=True,
    )
    renewal_count = fields.Integer(
        string='Renewals',
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
    @api.depends('risk_level', 'state')
    def _compute_color(self):
        for record in self:
            if record.risk_level == 'critical':
                record.color = 1
            elif record.risk_level == 'high':
                record.color = 2
            elif record.risk_level == 'medium':
                record.color = 3
            else:
                record.color = 4

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
                        _("Expiration Deadline cannot be earlier than the Effective Start Date.")
                    )

    @api.constrains('review_date', 'expiration_date')
    def _check_review_before_expiry(self):
        for record in self:
            if record.review_date and record.expiration_date:
                if record.review_date > record.expiration_date:
                    raise ValidationError(
                        _("Scheduled Review Date cannot be after the Expiration Deadline.")
                    )

    # -------------------------------------------------------------------------
    # CRUD OVERRIDES (Selective Stage-by-Stage Security Enforcements)
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', _('New')) == _('New'):
                vals['reference'] = self.env['ir.sequence'].next_by_code(
                    'security.exception.sequence'
                ) or _('New')
            # Force requester_id to the logged-in user for audit integrity
            vals['requester_id'] = self.env.user.id
        return super().create(vals_list)

    def write(self, vals):
        """Selective Security Control: Block regular users from modifying submitted records while allowing Reviewers/Managers to evaluate."""
        is_reviewer_or_above = (
            self.env.user.has_group('exceptrack_security.group_exceptrack_reviewer') or
            self.env.user.has_group('exceptrack_security.group_exceptrack_manager') or
            self.env.user.has_group('exceptrack_security.group_exceptrack_admin') or
            self.env.is_superuser() or
            self.env.context.get('sudo_workflow')
        )

        for record in self:
            # 1. Block regular users (Alice) from modifying records once submitted (state != 'draft')
            if record.state != 'draft' and not is_reviewer_or_above:
                user_updated_fields = set(vals.keys()) - {'message_follower_ids', 'activity_ids', 'message_ids'}
                if user_updated_fields:
                    raise UserError(_(
                        "Access Denied: Security exception '%s' has been submitted for assessment and cannot be modified by a regular user. "
                        "Please contact a Security Reviewer or Manager to request changes."
                    ) % record.name)

            # 2. Block regular users from manually modifying Reviewer or Approver assignments at ANY stage
            if ('reviewer_id' in vals or 'approver_id' in vals) and not is_reviewer_or_above:
                raise UserError(_(
                    "Access Denied: Only a Security Reviewer, Manager, or Administrator can assign or change Reviewers and Approvers."
                ))

        return super().write(vals)

    def unlink(self):
        """Strict Security Audit Protection: Block deletion of non-draft records."""
        is_admin = self.env.user.has_group('exceptrack_security.group_exceptrack_admin')
        for record in self:
            if record.state != 'draft' and not is_admin:
                raise UserError(_(
                    "Audit Compliance Violation: Security exception '%s' (%s) has passed the Draft stage and cannot be deleted. "
                    "Submitted exceptions must remain in the system for security audit history."
                ) % (record.name, record.reference))
            if record.state == 'draft' and record.requester_id != self.env.user and not is_admin:
                raise UserError(_(
                    "Access Denied: You can only delete Draft requests that you submitted yourself."
                ))
        return super().unlink()

    # -------------------------------------------------------------------------
    # WORKFLOW ACTIONS (True 50/50 Round-Robin Reviewer Alternation)
    # -------------------------------------------------------------------------
    def action_submit(self):
        """Draft → Assessment (True 50/50 Round-Robin Auto-Assignment among Reviewers)"""
        self.ensure_one()
        if not self.business_justification:
            raise UserError(
                _("Please enter a Business Justification before submitting for assessment.")
            )

        reviewers = self._get_group_users('exceptrack_security.group_exceptrack_reviewer')

        # Auto-assign Reviewer using True 50/50 Round-Robin alternation if not manually selected
        assigned_reviewer = False
        if not self.reviewer_id and reviewers:
            candidate_reviewers = reviewers.filtered(lambda u: u != self.env.user) or reviewers
            if len(candidate_reviewers) == 1:
                assigned_reviewer = candidate_reviewers[0]
            else:
                # Find the last submitted exception with an assigned reviewer to rotate to the next one
                last_exc = self.search([
                    ('reviewer_id', 'in', candidate_reviewers.ids)
                ], order='id desc', limit=1)
                if last_exc and last_exc.reviewer_id in candidate_reviewers:
                    last_idx = candidate_reviewers.ids.index(last_exc.reviewer_id.id)
                    next_idx = (last_idx + 1) % len(candidate_reviewers)
                    assigned_reviewer = candidate_reviewers[next_idx]
                else:
                    assigned_reviewer = candidate_reviewers[0]

        vals = {'state': 'assessment'}
        if assigned_reviewer:
            vals['reviewer_id'] = assigned_reviewer.id

        self.sudo().with_context(sudo_workflow=True).write(vals)

        # Post activity notifications to all active Security Reviewers
        for reviewer in reviewers:
            self.sudo().activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_("New Security Exception Pending Assessment"),
                note=_(
                    "Security exception '%s' (%s) submitted by %s requires security assessment."
                ) % (self.name, self.reference, self.env.user.name),
                user_id=reviewer.id,
            )

    def action_assess(self):
        """Assessment → Review"""
        self.ensure_one()
        is_admin = self.env.user.has_group('exceptrack_security.group_exceptrack_admin')
        is_reviewer = self.env.user.has_group('exceptrack_security.group_exceptrack_reviewer')
        if not (is_reviewer or is_admin):
            raise UserError(
                _("Access Denied: Only a Security Reviewer or Administrator can complete security assessment.")
            )
        if not self.reviewer_id:
            raise UserError(
                _("Please assign a Security Reviewer before completing assessment.")
            )
        self.sudo().with_context(sudo_workflow=True).write({'state': 'review'})

    def action_recommend_approval(self):
        """Review → Pending Approval (Round-Robin Manager Auto-Assignment)"""
        self.ensure_one()
        is_admin = self.env.user.has_group('exceptrack_security.group_exceptrack_admin')
        is_reviewer = self.env.user.has_group('exceptrack_security.group_exceptrack_reviewer')
        if not (is_reviewer or is_admin):
            raise UserError(
                _("Access Denied: Only a Security Reviewer or Administrator can recommend approval.")
            )

        managers = self._get_group_users('exceptrack_security.group_exceptrack_manager')

        # Auto-assign Manager using Round-Robin if not manually selected
        assigned_approver = False
        if not self.approver_id and managers:
            candidate_managers = managers.filtered(lambda u: u != self.env.user and u != self.requester_id) or managers
            if len(candidate_managers) == 1:
                assigned_approver = candidate_managers[0]
            else:
                last_exc = self.search([
                    ('approver_id', 'in', candidate_managers.ids)
                ], order='id desc', limit=1)
                if last_exc and last_exc.approver_id in candidate_managers:
                    last_idx = candidate_managers.ids.index(last_exc.approver_id.id)
                    next_idx = (last_idx + 1) % len(candidate_managers)
                    assigned_approver = candidate_managers[next_idx]
                else:
                    assigned_approver = candidate_managers[0]

        vals = {'state': 'pending_approval'}
        if assigned_approver:
            vals['approver_id'] = assigned_approver.id

        self.sudo().with_context(sudo_workflow=True).write(vals)

        target_approver = self.approver_id or assigned_approver
        if not target_approver:
            raise UserError(
                _("Please assign an Approving Manager before recommending approval.")
            )

        # Post activity notification to Approving Manager
        if target_approver:
            self.sudo().activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_("Security Exception Pending Approval"),
                note=_(
                    "Security exception '%s' (%s) recommended for approval by %s. Please review and approve/reject."
                ) % (self.name, self.reference, self.env.user.name),
                user_id=target_approver.id,
            )

    def action_approve(self):
        """Pending Approval → Active (Separation of Duties Enforced)"""
        self.ensure_one()
        is_admin = self.env.user.has_group('exceptrack_security.group_exceptrack_admin')
        is_manager = self.env.user.has_group('exceptrack_security.group_exceptrack_manager')

        # 1. Role Check
        if not (is_manager or is_admin):
            raise UserError(
                _("Access Denied: Only an Approving Manager or Administrator can approve security exceptions.")
            )

        # 2. Separation of Duties Check: Submitter cannot self-approve unless Admin
        if self.requester_id == self.env.user and not is_admin:
            raise UserError(
                _("Separation of Duties Violation: You submitted this exception request yourself. An independent Manager must review and approve it.")
            )

        if not self.start_date or not self.expiration_date:
            raise UserError(
                _("Both Start Date and Expiration Deadline are required before activation.")
            )
        self.sudo().with_context(sudo_workflow=True).write({'state': 'active'})

    def action_reject(self):
        """Review / Pending Approval → Rejected"""
        self.ensure_one()
        is_admin = self.env.user.has_group('exceptrack_security.group_exceptrack_admin')
        is_reviewer = self.env.user.has_group('exceptrack_security.group_exceptrack_reviewer')
        is_manager = self.env.user.has_group('exceptrack_security.group_exceptrack_manager')

        if not (is_reviewer or is_manager or is_admin):
            raise UserError(
                _("Access Denied: Only a Security Reviewer, Manager, or Administrator can reject requests.")
            )
        if self.state not in ('review', 'pending_approval'):
            raise UserError(
                _("Rejection is only allowed during Review or Pending Approval stages.")
            )
        self.sudo().with_context(sudo_workflow=True).write({'state': 'rejected'})

    def action_revise(self):
        """Rejected → Draft (Allows Requester to edit & resubmit)"""
        self.ensure_one()
        if self.state != 'rejected':
            raise UserError(
                _("Only rejected exceptions can be revised.")
            )
        self.sudo().with_context(sudo_workflow=True).write({'state': 'draft'})

    def action_initiate_review(self):
        """Active → Under Review"""
        self.ensure_one()
        is_admin = self.env.user.has_group('exceptrack_security.group_exceptrack_admin')
        is_reviewer = self.env.user.has_group('exceptrack_security.group_exceptrack_reviewer')
        is_manager = self.env.user.has_group('exceptrack_security.group_exceptrack_manager')
        if not (is_reviewer or is_manager or is_admin):
            raise UserError(
                _("Access Denied: Only a Security Reviewer, Manager, or Administrator can initiate periodic review.")
            )
        self.sudo().with_context(sudo_workflow=True).write({'state': 'under_review'})

    def action_renew(self):
        """Under Review → Active (Renewal)"""
        self.ensure_one()
        is_admin = self.env.user.has_group('exceptrack_security.group_exceptrack_admin')
        is_manager = self.env.user.has_group('exceptrack_security.group_exceptrack_manager')
        if not (is_manager or is_admin):
            raise UserError(
                _("Access Denied: Only an Approving Manager or Administrator can grant exception renewals.")
            )
        if self.state != 'under_review':
            raise UserError(
                _("Only exceptions under review can be renewed.")
            )
        self.sudo().with_context(sudo_workflow=True).write({
            'state': 'active',
            'renewal_count': self.renewal_count + 1,
        })
        self.message_post(
            body=_("🔄 Exception renewed (Renewal #%d).") % self.renewal_count,
            message_type='comment',
            subtype_xmlid='mail.mt_note',
        )

    def action_request_verification(self):
        """Under Review → Pending Verification"""
        self.ensure_one()
        is_admin = self.env.user.has_group('exceptrack_security.group_exceptrack_admin')
        is_reviewer = self.env.user.has_group('exceptrack_security.group_exceptrack_reviewer')
        if not (is_reviewer or is_admin):
            raise UserError(
                _("Access Denied: Only a Security Reviewer or Administrator can request remediation verification.")
            )
        if self.state != 'under_review':
            raise UserError(
                _("Verification can only be requested for exceptions under review.")
            )
        self.sudo().with_context(sudo_workflow=True).write({
            'state': 'pending_verification',
            'verification_result': False,
            'verified_by_id': False,
            'verification_date': False,
            'verification_notes': False,
        })

    def action_verify_pass(self):
        """Pending Verification → Closed (Pass)"""
        self.ensure_one()
        is_admin = self.env.user.has_group('exceptrack_security.group_exceptrack_admin')
        is_reviewer = self.env.user.has_group('exceptrack_security.group_exceptrack_reviewer')
        if not (is_reviewer or is_admin):
            raise UserError(
                _("Access Denied: Only a Security Reviewer or Administrator can perform remediation verification.")
            )
        if self.requester_id == self.env.user and not is_admin:
            raise UserError(
                _("Separation of Duties Violation: You cannot verify the remediation of an exception that you requested yourself!")
            )
        if self.state != 'pending_verification':
            raise UserError(
                _("Verification is only possible when pending verification.")
            )
        if not self.verification_notes:
            raise UserError(
                _("Please record your Verification Findings in the Verification tab before closing.")
            )
        self.sudo().with_context(sudo_workflow=True).write({
            'state': 'closed',
            'verification_result': 'pass',
            'verified_by_id': self.env.user.id,
            'verification_date': date.today(),
        })

    def action_verify_fail(self):
        """Pending Verification → Active (Fail)"""
        self.ensure_one()
        is_admin = self.env.user.has_group('exceptrack_security.group_exceptrack_admin')
        is_reviewer = self.env.user.has_group('exceptrack_security.group_exceptrack_reviewer')
        if not (is_reviewer or is_admin):
            raise UserError(
                _("Access Denied: Only a Security Reviewer or Administrator can perform remediation verification.")
            )
        if self.state != 'pending_verification':
            raise UserError(
                _("Verification is only possible when pending verification.")
            )
        if not self.verification_notes:
            raise UserError(
                _("Please record your Verification Findings in the Verification tab.")
            )
        self.sudo().with_context(sudo_workflow=True).write({
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
                    summary=_("Security Exception Expiring Soon"),
                    note=_(
                        "Security exception '%s' (%s) expires on %s. "
                        "Please initiate review and remediation verification."
                    ) % (record.name, record.reference, record.expiration_date),
                    user_id=(record.owner_id or record.requester_id).id,
                )
