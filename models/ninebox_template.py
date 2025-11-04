from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class OHAppraisalNineboxTemplate(models.Model):
    _name = 'oh.appraisal.ninebox.template'
    _description = '9-Box Grid Assessment Template'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Template Name', required=True, tracking=True)
    department_id = fields.Many2one('hr.department', string='Department', tracking=True)
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


    @api.depends('department_id')
    def _compute_weightage_distribution(self):
        for record in self:
            if record.department_id:
                # Get weightage from department configuration
                dept_config = self.env['oh.appraisal.department.weightage'].search([
                    ('department_id', '=', record.department_id.id),
                    ('active', '=', True)
                ], limit=1)
                
                if dept_config:
                    # Using the correct field names from oh.appraisal.department.weightage model
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

    @api.constrains('performance_dept_line_ids', 'performance_role_line_ids', 'performance_common_line_ids',
                    'potential_dept_line_ids', 'potential_role_line_ids', 'potential_common_line_ids')
    def _check_weightage_distribution(self):
        for record in self:
            # Check Performance weightages
            dept_total = sum(record.performance_dept_line_ids.mapped('distributed_weightage'))
            role_total = sum(record.performance_role_line_ids.mapped('distributed_weightage'))
            common_total = sum(record.performance_common_line_ids.mapped('distributed_weightage'))
            
            if dept_total > record.dept_weightage:
                raise ValidationError(_('Total department performance weightage cannot exceed %s%%') % record.dept_weightage)
            if role_total > record.role_weightage:
                raise ValidationError(_('Total role performance weightage cannot exceed %s%%') % record.role_weightage)
            if common_total > record.common_weightage:
                raise ValidationError(_('Total common performance weightage cannot exceed %s%%') % record.common_weightage)

            # Check Potential weightages
            dept_total = sum(record.potential_dept_line_ids.mapped('distributed_weightage'))
            role_total = sum(record.potential_role_line_ids.mapped('distributed_weightage'))
            common_total = sum(record.potential_common_line_ids.mapped('distributed_weightage'))
            
            if dept_total > record.dept_weightage:
                raise ValidationError(_('Total department potential weightage cannot exceed %s%%') % record.dept_weightage)
            if role_total > record.role_weightage:
                raise ValidationError(_('Total role potential weightage cannot exceed %s%%') % record.role_weightage)
            if common_total > record.common_weightage:
                raise ValidationError(_('Total common potential weightage cannot exceed %s%%') % record.common_weightage)

    is_synced = fields.Boolean('Is Synced', default=False)

    @api.onchange('department_id')
    def _onchange_department_id(self):
        self.selected_okr_template_id = False

    def action_sync_key_results(self):
        """Sync Key Results from selected OKR template"""
        self.ensure_one()
        if not self.department_id or not self.selected_okr_template_id:
            return

        # Clear existing performance lines
        self.performance_dept_line_ids.unlink()
        self.performance_role_line_ids.unlink()
        self.performance_common_line_ids.unlink()

        okr_template = self.selected_okr_template_id

        # Sync department key results
        for kr in okr_template.department_key_result_ids:
            self.env['oh.appraisal.ninebox.performance.line'].create({
                'template_id': self.id,
                'category': 'department',
                'objective_breakdown': kr.key_objective_breakdown.objective_item,
                'priority': kr.breakdown_priority,
                'team_id': kr.team_id.id,
                'metric': kr.metric,
                'actual_value': kr.actual_value,
                'target_value': kr.target_value,
                'distributed_weightage': kr.distributed_weightage,
            })

        # Sync role key results
        for kr in okr_template.role_key_result_ids:
            self.env['oh.appraisal.ninebox.performance.line'].create({
                'template_id': self.id,
                'category': 'role',
                'objective_breakdown': kr.key_objective_breakdown.objective_item,
                'priority': kr.breakdown_priority,
                'team_id': kr.team_id.id,
                'metric': kr.metric,
                'actual_value': kr.actual_value,
                'target_value': kr.target_value,
                'distributed_weightage': kr.distributed_weightage,
            })

        # Sync common key results
        for kr in okr_template.common_key_result_ids:
            self.env['oh.appraisal.ninebox.performance.line'].create({
                'template_id': self.id,
                'category': 'common',
                'objective_breakdown': kr.key_objective_breakdown.objective_item,
                'priority': kr.breakdown_priority,
                'team_id': kr.team_id.id,
                'metric': kr.metric,
                'actual_value': kr.actual_value,
                'target_value': kr.target_value,
                'distributed_weightage': kr.distributed_weightage,
            })

        self.is_synced = True
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

        # Return a success message
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
    team_id = fields.Many2one('oh.appraisal.team', string='Team')  # Using OKR template's team model
    metric = fields.Char('Metric/Measure')
    actual_value = fields.Float('Actual Value')
    target_value = fields.Float('Target Value')
    progress = fields.Float('Progress (%)', compute='_compute_progress', store=True)
    distributed_weightage = fields.Float('Distributed Weightage (%)')

    @api.depends('actual_value', 'target_value')
    def _compute_progress(self):
        for record in self:
            if record.target_value:
                record.progress = (record.actual_value / record.target_value) * 100
            else:
                record.progress = 0.0

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
    team_id = fields.Many2one('oh.appraisal.team', string='Team')  # Using OKR template's team model
    metric = fields.Char('Metric/Measure')
    actual_value = fields.Float('Actual Value')
    target_value = fields.Float('Target Value')
    progress = fields.Float('Progress (%)', compute='_compute_progress', store=True)
    distributed_weightage = fields.Float('Distributed Weightage (%)')

    @api.depends('actual_value', 'target_value')
    def _compute_progress(self):
        for record in self:
            if record.target_value:
                record.progress = (record.actual_value / record.target_value) * 100
            else:
                record.progress = 0.0