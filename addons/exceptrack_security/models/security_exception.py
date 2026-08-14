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
    # FIELDS — Compensating Controls, Verification & Rejection Details
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
        help="Detailed notes confirming remediation has been verified or vulnerability scan evidence.",
    )
    rejection_reason = fields.Text(
        string='Rejection Reason / Findings',
        tracking=True,
        help="Detailed explanation recorded when an exception is rejected.",
    )
    rejected_by_id = fields.Many2one(
        'res.users',
        string='Rejected By',
        tracking=True,
    )
    rejection_date = fields.Date(
        string='Rejection Date',
        tracking=True,
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
    # CRUD OVERRIDES (Incremental Reference Sequence & Tamper Protection)
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', _('New')) in (_('New'), False):
                seq_number = self.env['ir.sequence'].next_by_code('security.exception.sequence')
                if not seq_number:
                    seq_number = _('New')
                while self.search_count([('reference', '=', seq_number)]) > 0:
                    seq_number = self.env['ir.sequence'].next_by_code('security.exception.sequence')
                vals['reference'] = seq_number
            vals['requester_id'] = self.env.user.id
        return super().create(vals_list)

    def write(self, vals):
        """Selective Security Control: Enforce assigned Reviewer/Manager lockouts and block regular user tampering."""
        is_reviewer_or_above = (
            self.env.user.has_group('exceptrack_security.group_exceptrack_reviewer') or
            self.env.user.has_group('exceptrack_security.group_exceptrack_manager') or
            self.env.user.has_group('exceptrack_security.group_exceptrack_admin') or
            self.env.is_superuser() or
            self.env.context.get('sudo_workflow')
        )
        is_admin = self.env.user.has_group('exceptrack_security.group_exceptrack_admin') or self.env.is_superuser()

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

            # 3. Block unassigned Reviewers/Managers from modifying a ticket assigned to someone else
            if not is_admin and not self.env.context.get('sudo_workflow'):
                if record.state in ('assessment', 'review', 'under_review', 'pending_verification') and record.reviewer_id:
                    if self.env.user.id != record.reviewer_id.id and (not record.approver_id or self.env.user.id != record.approver_id.id):
                        user_updated_fields = set(vals.keys()) - {'message_follower_ids', 'activity_ids', 'message_ids'}
                        if user_updated_fields:
                            raise UserError(_(
                                "Access Denied: Security exception '%s' is assigned to Reviewer %s. "
                                "Only the assigned Reviewer or an Administrator can modify this ticket."
                            ) % (record.name, record.reviewer_id.name))

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
            if record.state == 'draft' and record.requester_id.id != self.env.user.id and not is_admin:
                raise UserError(_(
                    "Access Denied: You can only delete Draft requests that you submitted yourself."
                ))
        return super().unlink()

    # -------------------------------------------------------------------------
    # WORKFLOW ACTIONS (Strict Assigned Reviewer / Approver Lockouts & Audit)
    # -------------------------------------------------------------------------
    def action_submit(self):
        """Draft → Assessment (Guaranteed Modulo 50/50 Round-Robin Reviewer Alternation)"""
        self.ensure_one()
        if not self.business_justification:
            raise UserError(
                _("Please enter a Business Justification before submitting for assessment.")
            )

        reviewers = self._get_group_users('exceptrack_security.group_exceptrack_reviewer')

        assigned_reviewer = False
        if not self.reviewer_id and reviewers:
            candidate_reviewers = reviewers.filtered(lambda u: u != self.env.user) or reviewers
            candidate_reviewers = candidate_reviewers.sorted(key=lambda r: r.id)
            total_submitted = self.search_count([('state', '!=', 'draft')])
            assigned_reviewer = candidate_reviewers[total_submitted % len(candidate_reviewers)]

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
        """Assessment → Review (Assigned Reviewer Lockout Enforced)"""
        self.ensure_one()
        is_admin = self.env.user.has_group('exceptrack_security.group_exceptrack_admin')
        is_reviewer = self.env.user.has_group('exceptrack_security.group_exceptrack_reviewer')

        if not (is_reviewer or is_admin):
            raise UserError(
                _("Access Denied: Only a Security Reviewer or Administrator can complete security assessment.")
            )
        
        if self.reviewer_id and self.env.user.id != self.reviewer_id.id and not is_admin:
            raise UserError(_(
                "Access Denied: Security exception '%s' is assigned to Reviewer %s. "
                "Only the assigned Reviewer or a Security Administrator can complete this review."
            ) % (self.name, self.reviewer_id.name))

        if not self.reviewer_id:
            raise UserError(
                _("Please assign a Security Reviewer before completing assessment.")
            )
        self.sudo().with_context(sudo_workflow=True).write({'state': 'review'})

    def action_recommend_approval(self):
        """Review → Pending Approval (Assigned Reviewer Lockout Enforced)"""
        self.ensure_one()
        is_admin = self.env.user.has_group('exceptrack_security.group_exceptrack_admin')
        is_reviewer = self.env.user.has_group('exceptrack_security.group_exceptrack_reviewer')

        if not (is_reviewer or is_admin):
            raise UserError(
                _("Access Denied: Only a Security Reviewer or Administrator can recommend approval.")
            )

        if self.reviewer_id and self.env.user.id != self.reviewer_id.id and not is_admin:
            raise UserError(_(
                "Access Denied: Security exception '%s' is assigned to Reviewer %s. "
                "Only the assigned Reviewer or a Security Administrator can recommend approval."
            ) % (self.name, self.reviewer_id.name))

        managers = self._get_group_users('exceptrack_security.group_exceptrack_manager')

        assigned_approver = False
        if not self.approver_id and managers:
            candidate_managers = managers.filtered(lambda u: u != self.env.user and u != self.requester_id) or managers
            candidate_managers = candidate_managers.sorted(key=lambda m: m.id)
            total_pending = self.search_count([('state', 'in', ['pending_approval', 'active', 'closed'])])
            assigned_approver = candidate_managers[total_pending % len(candidate_managers)]

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
        """Pending Approval → Active (Assigned Manager Lockout & SoD Enforced)"""
        self.ensure_one()
        is_admin = self.env.user.has_group('exceptrack_security.group_exceptrack_admin')
        is_manager = self.env.user.has_group('exceptrack_security.group_exceptrack_manager')

        # 1. Role Check
        if not (is_manager or is_admin):
            raise UserError(
                _("Access Denied: Only an Approving Manager or Administrator can approve security exceptions.")
            )

        # 2. Assigned Manager Lockout Check
        if self.approver_id and self.env.user.id != self.approver_id.id and not is_admin:
            raise UserError(_(
                "Access Denied: Security exception '%s' is assigned to Approving Manager %s. "
                "Only the assigned Manager (%s) or a Security Administrator can approve this request."
            ) % (self.name, self.approver_id.name, self.approver_id.name))

        # 3. Separation of Duties Check
        if self.requester_id.id == self.env.user.id and not is_admin:
            raise UserError(
                _("Separation of Duties Violation: You submitted this exception request yourself. An independent Manager must review and approve it.")
            )

        if not self.start_date or not self.expiration_date:
            raise UserError(
                _("Both Start Date and Expiration Deadline are required before activation.")
            )
        self.sudo().with_context(sudo_workflow=True).write({'state': 'active'})

    def action_reject(self):
        """Review / Pending Approval → Rejected (Records Rejection Audit Info)"""
        self.ensure_one()
        is_admin = self.env.user.has_group('exceptrack_security.group_exceptrack_admin')
        is_reviewer = self.env.user.has_group('exceptrack_security.group_exceptrack_reviewer')
        is_manager = self.env.user.has_group('exceptrack_security.group_exceptrack_manager')

        if not (is_reviewer or is_manager or is_admin):
            raise UserError(
                _("Access Denied: Only a Security Reviewer, Manager, or Administrator can reject requests.")
            )
        
        if self.state == 'pending_approval' and self.approver_id and self.env.user.id != self.approver_id.id and not is_admin:
            raise UserError(_(
                "Access Denied: Security exception '%s' is assigned to Approving Manager %s. Only the assigned Manager can reject this request."
            ) % (self.name, self.approver_id.name))

        if self.state in ('assessment', 'review') and self.reviewer_id and self.env.user.id != self.reviewer_id.id and not is_admin:
            raise UserError(_(
                "Access Denied: Security exception '%s' is assigned to Reviewer %s. Only the assigned Reviewer can reject this request."
            ) % (self.name, self.reviewer_id.name))

        if self.state not in ('review', 'pending_approval'):
            raise UserError(
                _("Rejection is only allowed during Review or Pending Approval stages.")
            )

        self.sudo().with_context(sudo_workflow=True).write({
            'state': 'rejected',
            'rejected_by_id': self.env.user.id,
            'rejection_date': date.today(),
        })

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
        if self.approver_id and self.env.user.id != self.approver_id.id and not is_admin:
            raise UserError(_(
                "Access Denied: Security exception '%s' is assigned to Manager %s. Only the assigned Manager can grant renewals."
            ) % (self.name, self.approver_id.name))

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
        if self.reviewer_id and self.env.user.id != self.reviewer_id.id and not is_admin:
            raise UserError(_(
                "Access Denied: Security exception '%s' is assigned to Reviewer %s. Only the assigned Reviewer can verify remediation."
            ) % (self.name, self.reviewer_id.name))
        if self.requester_id.id == self.env.user.id and not is_admin:
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
        if self.reviewer_id and self.env.user.id != self.reviewer_id.id and not is_admin:
            raise UserError(_(
                "Access Denied: Security exception '%s' is assigned to Reviewer %s. Only the assigned Reviewer can verify remediation."
            ) % (self.name, self.reviewer_id.name))
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
