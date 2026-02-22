# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class OHAppraisalNineboxTemplate(models.Model):
    _name = 'oh.appraisal.ninebox.template'
    _description = '9-Box Grid Assessment Template'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        'Template Name', 
        required=True, 
        tracking=True,
        help="Give your template a unique, descriptive name"
    )
    industry_type = fields.Many2one(
        'oh.appraisal.industry',
        string='Industry Type',
        index=True,
        tracking=True,
        help="Select the industry type to fetch the configured weightages from the Master Template"
    )
    department_id = fields.Many2one(
        'hr.department', 
        string='Department', 
        tracking=True,
        required=True,
        help="Select department to automatically load weightage configuration"
    )
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    # Weightage Distribution
    dept_weightage = fields.Float(string='Department Weightage (%)', compute='_compute_weightage_distribution', store=True)
    role_weightage = fields.Float(string='Role Weightage (%)', compute='_compute_weightage_distribution', store=True)
    common_weightage = fields.Float(string='Common Weightage (%)', compute='_compute_weightage_distribution', store=True)
    
    # Performance Lines
    performance_dept_line_ids = fields.One2many(
        'oh.appraisal.ninebox.performance.line',
        'template_id',
        domain=[('category', '=', 'department')],
        context={'default_category': 'department'}
    )
    performance_role_line_ids = fields.One2many(
        'oh.appraisal.ninebox.performance.line',
        'template_id',
        domain=[('category', '=', 'role')],
        context={'default_category': 'role'}
    )
    performance_common_line_ids = fields.One2many(
        'oh.appraisal.ninebox.performance.line',
        'template_id',
        domain=[('category', '=', 'common')],
        context={'default_category': 'common'}
    )

    # Potential Lines
    potential_dept_line_ids = fields.One2many(
        'oh.appraisal.ninebox.potential.line',
        'template_id',
        domain=[('category', '=', 'department')],
        context={'default_category': 'department'}
    )
    potential_role_line_ids = fields.One2many(
        'oh.appraisal.ninebox.potential.line',
        'template_id',
        domain=[('category', '=', 'role')],
        context={'default_category': 'role'}
    )
    potential_common_line_ids = fields.One2many(
        'oh.appraisal.ninebox.potential.line',
        'template_id',
        domain=[('category', '=', 'common')],
        context={'default_category': 'common'}
    )

    selected_okr_template_id = fields.Many2one(
        'oh.appraisal.okr.template',
        string='OKR Template',
        domain="[('department_id', '=', department_id), ('active', '=', True)]"
    )

    
    # Split ratio fields
    performance_split = fields.Float(
        'Performance Split (%)', 
        tracking=True,
        required=True,
        help="Portion of department weightage allocated to performance criteria"
    )
    potential_split = fields.Float(
        'Potential Split (%)', 
        tracking=True,
        required=True,
        help="Portion of department weightage allocated to potential criteria"
    )

    # Split weightage fields
    performance_dept_weightage = fields.Float(
        'Performance Department Weightage (%)',
        compute='_compute_split_weightages',
        store=True
    )
    potential_dept_weightage = fields.Float(
        'Potential Department Weightage (%)',
        compute='_compute_split_weightages',
        store=True
    )

    # Weightage distribution tables
    performance_weightage_ids = fields.One2many(
        'oh.appraisal.ninebox.weightage',
        'template_id',
        domain=[('type', '=', 'performance')],
        context={'default_type': 'performance'}
    )
    potential_weightage_ids = fields.One2many(
        'oh.appraisal.ninebox.weightage',
        'template_id',
        domain=[('type', '=', 'potential')],
        context={'default_type': 'potential'}
    )

    # Summary fields for display in tables
    performance_dept_available = fields.Float(
        'Performance Dept Available (%)',
        compute='_compute_summary_weightages'
    )
    performance_role_available = fields.Float(
        'Performance Role Available (%)',
        compute='_compute_summary_weightages'
    )
    performance_common_available = fields.Float(
        'Performance Common Available (%)',
        compute='_compute_summary_weightages'
    )
    
    potential_dept_available = fields.Float(
        'Potential Dept Available (%)',
        compute='_compute_summary_weightages'
    )
    potential_role_available = fields.Float(
        'Potential Role Available (%)',
        compute='_compute_summary_weightages'
    )
    potential_common_available = fields.Float(
        'Potential Common Available (%)',
        compute='_compute_summary_weightages'
    )

    # Allocated to Teams - sum from weightage distribution table itself
    performance_allocated_dept = fields.Float(
        'Performance Allocated Dept (%)',
        compute='_compute_allocated_to_teams',
        store=True
    )
    performance_allocated_role = fields.Float(
        'Performance Allocated Role (%)',
        compute='_compute_allocated_to_teams',
        store=True
    )
    performance_allocated_common = fields.Float(
        'Performance Allocated Common (%)',
        compute='_compute_allocated_to_teams',
        store=True
    )
    
    potential_allocated_dept = fields.Float(
        'Potential Allocated Dept (%)',
        compute='_compute_allocated_to_teams',
        store=True
    )
    potential_allocated_role = fields.Float(
        'Potential Allocated Role (%)',
        compute='_compute_allocated_to_teams',
        store=True
    )
    potential_allocated_common = fields.Float(
        'Potential Allocated Common (%)',
        compute='_compute_allocated_to_teams',
        store=True
    )

    @api.depends('performance_weightage_ids.department_weightage',
                 'performance_weightage_ids.role_weightage',
                 'performance_weightage_ids.common_weightage',
                 'potential_weightage_ids.department_weightage',
                 'potential_weightage_ids.role_weightage',
                 'potential_weightage_ids.common_weightage')
    def _compute_summary_weightages(self):
        """Compute total available weightages from distribution tables - for criteria tables"""
        for record in self:
            # Performance - sum from weightage distribution table (for criteria tables)
            record.performance_dept_available = sum(record.performance_weightage_ids.mapped('department_weightage'))
            record.performance_role_available = sum(record.performance_weightage_ids.mapped('role_weightage'))
            record.performance_common_available = sum(record.performance_weightage_ids.mapped('common_weightage'))
            
            # Potential - sum from weightage distribution table (for criteria tables)
            record.potential_dept_available = sum(record.potential_weightage_ids.mapped('department_weightage'))
            record.potential_role_available = sum(record.potential_weightage_ids.mapped('role_weightage'))
            record.potential_common_available = sum(record.potential_weightage_ids.mapped('common_weightage'))

    @api.depends('performance_weightage_ids.department_weightage',
                 'performance_weightage_ids.role_weightage',
                 'performance_weightage_ids.common_weightage',
                 'potential_weightage_ids.department_weightage',
                 'potential_weightage_ids.role_weightage',
                 'potential_weightage_ids.common_weightage')
    def _compute_allocated_to_teams(self):
        """Compute allocated to teams from weightage distribution table ONLY - for display in header"""
        for record in self:
            # Performance - sum from the weightage distribution table rows only
            record.performance_allocated_dept = sum(record.performance_weightage_ids.mapped('department_weightage'))
            record.performance_allocated_role = sum(record.performance_weightage_ids.mapped('role_weightage'))
            record.performance_allocated_common = sum(record.performance_weightage_ids.mapped('common_weightage'))
            
            # Potential - sum from the weightage distribution table rows only
            record.potential_allocated_dept = sum(record.potential_weightage_ids.mapped('department_weightage'))
            record.potential_allocated_role = sum(record.potential_weightage_ids.mapped('role_weightage'))
            record.potential_allocated_common = sum(record.potential_weightage_ids.mapped('common_weightage'))

    def _ensure_common_weightage_distribution(self):
        """Trigger recomputation of common weightage"""
        self.mapped('performance_weightage_ids')._compute_common_weightage()
        self.mapped('potential_weightage_ids')._compute_common_weightage()

    @api.constrains('performance_split', 'potential_split')
    def _check_split_total(self):
        for record in self:
            if not record.dept_weightage:
                continue
                
            total_split = (record.performance_split or 0.0) + (record.potential_split or 0.0)
            if total_split > record.dept_weightage:
                raise ValidationError(_(
                    'Total of Performance (%s%%) and Potential (%s%%) splits cannot exceed '
                    'the available Department weightage (%s%%)'
                ) % (record.performance_split, record.potential_split, record.dept_weightage))
            
            if record.performance_split < 0 or record.potential_split < 0:
                raise ValidationError(_('Split percentages cannot be negative'))

    @api.onchange('performance_split', 'potential_split')
    def _onchange_splits(self):
        for record in self:
            if not record.dept_weightage:
                record.performance_split = 0.0
                record.potential_split = 0.0
                return

            if record.performance_split or record.potential_split:
                total = (record.performance_split or 0.0) + (record.potential_split or 0.0)
                if total > record.dept_weightage:
                    excess = total - record.dept_weightage
                    if record.potential_split:
                        record.potential_split = max(0, record.potential_split - excess)

    @api.depends('department_id', 'industry_type')
    def _compute_weightage_distribution(self):
        for record in self:
            if record.department_id:
                domain = [
                    ('department_id', '=', record.department_id.id),
                    ('active', '=', True),
                ]
                if record.industry_type:
                    domain.append(('industry_type', '=', record.industry_type.id))
                dept_config = self.env['oh.appraisal.department.weightage'].search(
                    domain, limit=1
                )
                # Fallback: if no config found with industry, try without
                if not dept_config and record.industry_type:
                    dept_config = self.env['oh.appraisal.department.weightage'].search([
                        ('department_id', '=', record.department_id.id),
                        ('active', '=', True),
                    ], limit=1)
                
                if dept_config:
                    record.dept_weightage = dept_config.functional_weightage
                    record.role_weightage = dept_config.role_weightage
                    record.common_weightage = dept_config.common_weightage
                else:
                    record.dept_weightage = 0.0
                    record.role_weightage = 0.0
                    record.common_weightage = 0.0
            else:
                record.dept_weightage = 0.0
                record.role_weightage = 0.0
                record.common_weightage = 0.0

    is_synced = fields.Boolean('Is Synced', default=False)

    @api.onchange('department_id', 'industry_type')
    def _onchange_department_id(self):
        self.selected_okr_template_id = False
        self.performance_split = 0.0
        self.potential_split = 0.0

    def action_sync_key_results(self):
        """Sync Key Results and Weightages from selected OKR template"""
        self.ensure_one()
        if not self.department_id or not self.selected_okr_template_id:
            return

        okr_template = self.selected_okr_template_id

        # Clear existing records
        self.performance_weightage_ids.unlink()
        self.performance_dept_line_ids.unlink()
        self.performance_role_line_ids.unlink()
        self.performance_common_line_ids.unlink()

        # 1. First sync master weightages
        self.performance_split = okr_template.department_budget_functional
        self.role_weightage = okr_template.department_budget_role
        self.common_weightage = okr_template.department_budget_common

        # 2. Sync weightage distribution from OKR template's weightage table
        existing_teams = {}
        for okr_weightage in okr_template.weightage_ids:
            weightage_vals = {
                'template_id': self.id,
                'team_id': okr_weightage.team_id.id,
                'type': 'performance',
                'department_weightage': okr_weightage.department_weightage,
                'role_weightage': okr_weightage.role_weightage,
            }
            weightage = self.env['oh.appraisal.ninebox.weightage'].create(weightage_vals)
            existing_teams[okr_weightage.team_id.id] = weightage

        # 3. Sync key results with exact values
        # Department key results
        for kr in okr_template.department_key_result_ids:
            if kr.team_id.id in existing_teams:
                self.env['oh.appraisal.ninebox.performance.line'].create({
                    'template_id': self.id,
                    'category': 'department',
                    'objective_breakdown': kr.key_objective_breakdown.objective_item,
                    'priority': kr.breakdown_priority,
                    'team_id': kr.team_id.id,
                    'metric': kr.metric,
                    'actual_value': kr.actual_value,
                    'target_value': kr.target_value,
                    # 'achieve': '',
                    'distributed_weightage': kr.distributed_weightage,
                })

        # Role key results 
        for kr in okr_template.role_key_result_ids:
            if kr.team_id.id in existing_teams:
                self.env['oh.appraisal.ninebox.performance.line'].create({
                    'template_id': self.id,
                    'category': 'role',
                    'objective_breakdown': kr.key_objective_breakdown.objective_item,
                    'priority': kr.breakdown_priority,
                    'team_id': kr.team_id.id,
                    'metric': kr.metric,
                    'actual_value': kr.actual_value,
                    'target_value': kr.target_value,
                    # 'achieve': '',
                    'distributed_weightage': kr.distributed_weightage,
                })

        # Common key results
        for kr in okr_template.common_key_result_ids:
            if kr.team_id.id in existing_teams:
                self.env['oh.appraisal.ninebox.performance.line'].create({
                    'template_id': self.id,
                    'category': 'common',
                    'objective_breakdown': kr.key_objective_breakdown.objective_item,
                    'priority': kr.breakdown_priority,
                    'team_id': kr.team_id.id,
                    'metric': kr.metric,
                    'actual_value': kr.actual_value,
                    'target_value': kr.target_value,
                    # 'achieve': '',
                    'distributed_weightage': kr.distributed_weightage,
                })

        # Update computed fields and status
        self.is_synced = True
        self._compute_summary_weightages()
        self._compute_allocated_to_teams()
        self._compute_performance_distributed()
        self._ensure_common_weightage_distribution()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    @api.depends('is_synced', 'selected_okr_template_id')
    def _compute_sync_status(self):
        for record in self:
            if record.is_synced and record.selected_okr_template_id:
                record.sync_status = _('Synced with: %s') % record.selected_okr_template_id.name
            else:
                record.sync_status = _('Not synced')

    sync_status = fields.Char(
        string='Sync Status',
        compute='_compute_sync_status',
        store=True
    )

    # Add name uniqueness constraint per department
    _sql_constraints = [
        ('unique_name_per_department',
         'unique(name, department_id)',
         'Template name must be unique per department!')
    ]

    def action_unsync_key_results(self):
        """Unsync Key Results and clear performance tables"""
        self.ensure_one()
        
        message = ''
        if self.performance_dept_line_ids or self.performance_role_line_ids or self.performance_common_line_ids:
            # Clear all performance lines
            self.performance_dept_line_ids.unlink()
            self.performance_role_line_ids.unlink()
            self.performance_common_line_ids.unlink()
            message = _("Performance tables have been cleared successfully!")
        
        # Reset sync status and selected template
        self.write({
            'is_synced': False,
            'selected_okr_template_id': False
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': message or _('Tables are already empty'),
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
            }
        }

    # Performance currently distributed totals
    performance_dept_distributed = fields.Float(
        'Performance Department Distributed (%)', 
        compute='_compute_performance_distributed'
    )
    performance_role_distributed = fields.Float(
        'Performance Role Distributed (%)', 
        compute='_compute_performance_distributed'
    )
    performance_common_distributed = fields.Float(
        'Performance Common Distributed (%)', 
        compute='_compute_performance_distributed'
    )

    # Potential currently distributed totals
    potential_dept_distributed = fields.Float(
        'Potential Department Distributed (%)', 
        compute='_compute_potential_distributed'
    )
    potential_role_distributed = fields.Float(
        'Potential Role Distributed (%)', 
        compute='_compute_potential_distributed'
    )
    potential_common_distributed = fields.Float(
        'Potential Common Distributed (%)', 
        compute='_compute_potential_distributed'
    )

    @api.depends('performance_dept_line_ids.distributed_weightage',
                 'performance_role_line_ids.distributed_weightage',
                 'performance_common_line_ids.distributed_weightage')
    def _compute_performance_distributed(self):
        for record in self:
            record.performance_dept_distributed = sum(record.performance_dept_line_ids.mapped('distributed_weightage'))
            record.performance_role_distributed = sum(record.performance_role_line_ids.mapped('distributed_weightage'))
            record.performance_common_distributed = sum(record.performance_common_line_ids.mapped('distributed_weightage'))

    @api.constrains('performance_dept_line_ids', 'performance_role_line_ids', 'performance_common_line_ids')
    def _check_performance_weightage_limits(self):
        for record in self:
            total_dept = sum(record.performance_dept_line_ids.mapped('distributed_weightage'))
            total_role = sum(record.performance_role_line_ids.mapped('distributed_weightage'))
            total_common = sum(record.performance_common_line_ids.mapped('distributed_weightage'))

            if total_dept > record.performance_dept_available:
                raise ValidationError(_('Total department weightage (%.2f%%) cannot exceed available weightage (%.2f%%)') % (total_dept, record.performance_dept_available))
            if total_role > record.performance_role_available:
                raise ValidationError(_('Total role weightage (%.2f%%) cannot exceed available weightage (%.2f%%)') % (total_role, record.performance_role_available))
            if total_common > record.performance_common_available:
                raise ValidationError(_('Total common weightage (%.2f%%) cannot exceed available weightage (%.2f%%)') % (total_common, record.performance_common_available))

    @api.depends('potential_dept_line_ids.distributed_weightage',
                 'potential_role_line_ids.distributed_weightage',
                 'potential_common_line_ids.distributed_weightage')
    def _compute_potential_distributed(self):
        for record in self:
            record.potential_dept_distributed = sum(record.potential_dept_line_ids.mapped('distributed_weightage'))
            record.potential_role_distributed = sum(record.potential_role_line_ids.mapped('distributed_weightage'))
            record.potential_common_distributed = sum(record.potential_common_line_ids.mapped('distributed_weightage'))

    @api.constrains('potential_dept_line_ids', 'potential_role_line_ids', 'potential_common_line_ids')
    def _check_potential_weightage_limits(self):
        for record in self:
            total_dept = sum(record.potential_dept_line_ids.mapped('distributed_weightage'))
            total_role = sum(record.potential_role_line_ids.mapped('distributed_weightage'))
            total_common = sum(record.potential_common_line_ids.mapped('distributed_weightage'))

            if total_dept > record.potential_dept_available:
                raise ValidationError(_('Total department weightage (%.2f%%) cannot exceed available weightage (%.2f%%)') % (total_dept, record.potential_dept_available))
            if total_role > record.potential_role_available:
                raise ValidationError(_('Total role weightage (%.2f%%) cannot exceed available weightage (%.2f%%)') % (total_role, record.potential_role_available))
            if total_common > record.potential_common_available:
                raise ValidationError(_('Total common weightage (%.2f%%) cannot exceed available weightage (%.2f%%)') % (total_common, record.potential_common_available))

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._ensure_common_weightage_distribution()
        record._compute_allocated_to_teams()
        return record

    def write(self, vals):
        res = super().write(vals)
        if any(f in vals for f in ['common_weightage', 'performance_weightage_ids', 'potential_weightage_ids']):
            self._ensure_common_weightage_distribution()
            self._compute_allocated_to_teams()
        return res

    def _redistribute_common_weightage(self):
        """Redistribute common weightage equally among teams."""
        for record in self:
            # For Performance
            perf_teams = record.performance_weightage_ids
            if perf_teams:
                weight_per_team = record.common_weightage / len(perf_teams)
                weight_per_team = round(weight_per_team, 2)
                
                perf_teams.write({'common_weightage': weight_per_team})
                
                total_allocated = sum(perf_teams.mapped('common_weightage'))
                if abs(total_allocated - record.common_weightage) > 0.01:
                    difference = record.common_weightage - total_allocated
                    perf_teams[0].write({
                        'common_weightage': perf_teams[0].common_weightage + round(difference, 2)
                    })

            # For Potential
            pot_teams = record.potential_weightage_ids
            if pot_teams:
                weight_per_team = record.common_weightage / len(pot_teams)
                weight_per_team = round(weight_per_team, 2)
                
                pot_teams.write({'common_weightage': weight_per_team})
                
                total_allocated = sum(pot_teams.mapped('common_weightage'))
                if abs(total_allocated - record.common_weightage) > 0.01:
                    difference = record.common_weightage - total_allocated
                    pot_teams[0].write({
                        'common_weightage': pot_teams[0].common_weightage + round(difference, 2)
                    })

    @api.onchange('performance_weightage_ids', 'potential_weightage_ids')
    def _onchange_weightage_ids(self):
        """Trigger common weightage recalculation on team changes"""
        self._ensure_common_weightage_distribution()

    @api.constrains('performance_weightage_ids', 'potential_weightage_ids')
    def _check_common_weightage_totals(self):
        for record in self:
            # Check Performance
            perf_common_total = sum(record.performance_weightage_ids.mapped('common_weightage'))
            if abs(perf_common_total - record.common_weightage) > 0.01:
                record._ensure_common_weightage_distribution()

            # Check Potential
            pot_common_total = sum(record.potential_weightage_ids.mapped('common_weightage'))
            if abs(pot_common_total - record.common_weightage) > 0.01:
                record._ensure_common_weightage_distribution()


class OHAppraisalNineboxPerformanceLine(models.Model):
    _name = 'oh.appraisal.ninebox.performance.line'
    _description = '9-Box Performance Line'
    _order = 'sequence, id'

    sequence = fields.Integer('Sequence', default=10)
    template_id = fields.Many2one('oh.appraisal.ninebox.template', ondelete='cascade')
    category = fields.Selection([
        ('department', 'Department'),
        ('role', 'Role'),
        ('common', 'Common')
    ], required=True)
    
    objective_breakdown = fields.Char('Objective Breakdown', required=True)
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], default='medium')
    team_id = fields.Many2one('oh.appraisal.team', string='Team', required=True)
    metric = fields.Selection([
        ('percentage', 'Percentage (%)'),
        ('count', 'Count (Numeric)'),
        ('rating', 'Rating (Scale)'),
        ('score', 'Score (Points)')
    ], string='Metric/Measure', default=False,
    help="Select the type of measurement:\n"
         "• Percentage: Measured as percentage value (0-100%)\n"
         "• Count: Numeric count or quantity\n"
         "• Rating: Scale-based rating (e.g., 1-5, 1-10)\n"
         "• Score: Points-based scoring system\n"
         "• Leave blank if no specific metric applies")
    actual_value = fields.Float('Actual Value',
    help="Actual numeric value achieved/measured")
    target_value = fields.Float('Target Value', required=True,
    help="Target numeric value to be achieved")
    # achieve = fields.Char('Achieve',
    # help="Achievement status or assessment",
    # default='')
    distributed_weightage = fields.Float('Distributed Weightage (%)', required=True)

    @api.onchange('metric')
    def _onchange_metric(self):
        """Set default descriptions based on selected metric"""
        metric_descriptions = {
            'percentage': 'Measured as percentage (0-100%)',
            'count': 'Measured as numeric count/quantity',
            'rating': 'Measured on a rating scale',
            'score': 'Measured in points'
        }
        
        if self.metric and self.metric in metric_descriptions:
            pass  # Metric helper for future use


class OHAppraisalNineboxPotentialLine(models.Model):
    _name = 'oh.appraisal.ninebox.potential.line'
    _description = '9-Box Potential Line'
    _order = 'sequence, id'

    sequence = fields.Integer('Sequence', default=10)
    template_id = fields.Many2one('oh.appraisal.ninebox.template', ondelete='cascade')
    category = fields.Selection([
        ('department', 'Department'),
        ('role', 'Role'),
        ('common', 'Common')
    ], required=True)
    
    objective_breakdown = fields.Char('Objective Breakdown', required=True)
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], default='medium')
    team_id = fields.Many2one('oh.appraisal.team', string='Team', required=True)
    metric = fields.Selection([
        ('percentage', 'Percentage (%)'),
        ('count', 'Count (Numeric)'),
        ('rating', 'Rating (Scale)'),
        ('score', 'Score (Points)')
    ], string='Metric/Measure', default=False,
    help="Select the type of measurement:\n"
         "• Percentage: Measured as percentage value (0-100%)\n"
         "• Count: Numeric count or quantity\n"
         "• Rating: Scale-based rating (e.g., 1-5, 1-10)\n"
         "• Score: Points-based scoring system\n"
         "• Leave blank if no specific metric applies")
    actual_value = fields.Float('Actual Value',
    help="Actual numeric value achieved/measured")
    target_value = fields.Float('Target Value', required=True,
    help="Target numeric value to be achieved")
    # achieve = fields.Char('Achieve',
    # help="Achievement status or assessment",
    # default='')
    distributed_weightage = fields.Float('Distributed Weightage (%)', required=True)

    @api.onchange('metric')
    def _onchange_metric(self):
        """Set default descriptions based on selected metric"""
        metric_descriptions = {
            'percentage': 'Measured as percentage (0-100%)',
            'count': 'Measured as numeric count/quantity',
            'rating': 'Measured on a rating scale',
            'score': 'Measured in points'
        }
        
        if self.metric and self.metric in metric_descriptions:
            pass  # Metric helper for future use


class OHAppraisalNineboxWeightage(models.Model):
    _name = 'oh.appraisal.ninebox.weightage'
    _description = 'Nine Box Weightage Distribution'
    _order = 'sequence, id'

    sequence = fields.Integer('Sequence', default=10)
    template_id = fields.Many2one('oh.appraisal.ninebox.template', ondelete='cascade')
    team_id = fields.Many2one('oh.appraisal.team', string='Team', required=True)
    type = fields.Selection([
        ('performance', 'Performance'),
        ('potential', 'Potential')
    ], required=True)

    department_weightage = fields.Float('Department Weightage (%)')
    role_weightage = fields.Float('Role Weightage (%)')
    common_weightage = fields.Float(
        'Common Weightage (%)', 
        compute='_compute_common_weightage',
        store=True
    )

    @api.depends('template_id.common_weightage', 
                'template_id.performance_weightage_ids', 
                'template_id.potential_weightage_ids', 
                'type')
    def _compute_common_weightage(self):
        for record in self:
            if record.template_id and record.template_id.common_weightage:
                weightage_records = (record.template_id.performance_weightage_ids 
                                   if record.type == 'performance' 
                                   else record.template_id.potential_weightage_ids)
                team_count = len(weightage_records)
                if team_count > 0:
                    common_per_team = record.template_id.common_weightage / team_count
                    record.common_weightage = round(common_per_team, 2)
                else:
                    record.common_weightage = 0.0
            else:
                record.common_weightage = 0.0

    @api.model
    def create(self, vals):
        return super().create(vals)

    @api.constrains('department_weightage', 'role_weightage')
    def _check_edit_when_synced(self):
        for record in self:
            if record.template_id.is_synced:
                raise ValidationError(_("Cannot modify weightages while template is synced with OKR template"))

    def write(self, vals):
        # Prevent edits when synced except for common_weightage
        if self.template_id.is_synced and any(f in vals for f in ['department_weightage', 'role_weightage']):
            raise ValidationError(_("Cannot modify weightages while template is synced with OKR template"))
        return super().write(vals)