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

    
    # Split ratio fields
    performance_split = fields.Float(
        'Performance Split (%)', 
        tracking=True,
        help="Percentage of department weightage allocated to Performance"
    )
    potential_split = fields.Float(
        'Potential Split (%)', 
        tracking=True,
        help="Percentage of department weightage allocated to Potential"
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

    # Computed fields for available weightages
    performance_available_dept = fields.Float(
        'Available Performance Department (%)',
        compute='_compute_available_weightages'
    )
    performance_available_role = fields.Float(
        'Available Performance Role (%)',
        compute='_compute_available_weightages'
    )
    performance_available_common = fields.Float(
        'Available Performance Common (%)',
        compute='_compute_available_weightages'
    )
    
    potential_available_dept = fields.Float(
        'Available Potential Department (%)',
        compute='_compute_available_weightages'
    )
    potential_available_role = fields.Float(
        'Available Potential Role (%)',
        compute='_compute_available_weightages'
    )
    potential_available_common = fields.Float(
        'Available Potential Common (%)',
        compute='_compute_available_weightages'
    )

    @api.depends('performance_weightage_ids', 'potential_weightage_ids',
                'performance_split', 'potential_split',
                'dept_weightage', 'role_weightage', 'common_weightage')
    def _compute_available_weightages(self):
        for record in self:
            # Performance available
            perf_allocated_dept = sum(record.performance_weightage_ids.mapped('department_weightage'))
            perf_allocated_role = sum(record.performance_weightage_ids.mapped('role_weightage'))
            perf_allocated_common = sum(record.performance_weightage_ids.mapped('common_weightage'))

            record.performance_available_dept = record.performance_split - perf_allocated_dept
            record.performance_available_role = record.role_weightage - perf_allocated_role
            record.performance_available_common = record.common_weightage - perf_allocated_common

            # Potential available
            pot_allocated_dept = sum(record.potential_weightage_ids.mapped('department_weightage'))
            pot_allocated_role = sum(record.potential_weightage_ids.mapped('role_weightage'))
            pot_allocated_common = sum(record.potential_weightage_ids.mapped('common_weightage'))

            record.potential_available_dept = record.potential_split - pot_allocated_dept
            record.potential_available_role = record.role_weightage - pot_allocated_role
            record.potential_available_common = record.common_weightage - pot_allocated_common


    # @api.depends('dept_weightage', 'performance_split', 'potential_split')
    # def _compute_split_weightages(self):
    #     for record in self:
    #         record.performance_dept_weightage = record.dept_weightage * (record.performance_split / 100.0) if record.performance_split else 0.0
    #         record.potential_dept_weightage = record.dept_weightage * (record.potential_split / 100.0) if record.potential_split else 0.0

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
                return {
                    'warning': {
                        'title': _('Warning'),
                        'message': _('Please select a department first to get available weightage.')
                    }
                }

            if record.performance_split or record.potential_split:
                total = (record.performance_split or 0.0) + (record.potential_split or 0.0)
                if total > record.dept_weightage:
                    return {
                        'warning': {
                            'title': _('Warning'),
                            'message': _(
                                'Total of Performance and Potential splits (%s%%) cannot exceed '
                                'the available Department weightage (%s%%)'
                            ) % (total, record.dept_weightage)
                        }
                    }

    


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
        self.performance_split = 0.0
        self.potential_split = 0.0

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
    
    # Update the weightage distribution check for performance
    @api.constrains('performance_dept_line_ids')
    def _check_performance_weightage_distribution(self):
        for record in self:
            dept_total = sum(record.performance_dept_line_ids.mapped('distributed_weightage'))
            if dept_total > record.performance_dept_weightage:
                raise ValidationError(_('Total department performance weightage cannot exceed %s%%') % record.performance_dept_weightage)

    # Update the weightage distribution check for potential
    @api.constrains('potential_dept_line_ids')
    def _check_potential_weightage_distribution(self):
        for record in self:
            dept_total = sum(record.potential_dept_line_ids.mapped('distributed_weightage'))
            if dept_total > record.potential_dept_weightage:
                raise ValidationError(_('Total department potential weightage cannot exceed %s%%') % record.potential_dept_weightage)



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

    @api.depends('performance_dept_line_ids.distributed_weightage')
    def _compute_performance_distributed(self):
        for record in self:
            record.performance_dept_distributed = sum(record.performance_dept_line_ids.mapped('distributed_weightage'))
            record.performance_role_distributed = sum(record.performance_role_line_ids.mapped('distributed_weightage'))
            record.performance_common_distributed = sum(record.performance_common_line_ids.mapped('distributed_weightage'))

    @api.depends('potential_dept_line_ids.distributed_weightage')
    def _compute_potential_distributed(self):
        for record in self:
            record.potential_dept_distributed = sum(record.potential_dept_line_ids.mapped('distributed_weightage'))
            record.potential_role_distributed = sum(record.potential_role_line_ids.mapped('distributed_weightage'))
            record.potential_common_distributed = sum(record.potential_common_line_ids.mapped('distributed_weightage'))


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

    @api.constrains('distributed_weightage')
    def _check_distributed_weightage(self):
        for record in self:
            if record.category == 'department':
                available = record.template_id.performance_available_dept
                current = record.template_id.performance_dept_distributed
            elif record.category == 'role':
                available = record.template_id.performance_available_role
                current = record.template_id.performance_role_distributed
            else:  # common
                available = record.template_id.performance_available_common
                current = record.template_id.performance_common_distributed

            if current > available:
                raise ValidationError(_('Total distributed weightage cannot exceed available weightage of %s%%') % available)

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

    @api.constrains('distributed_weightage')
    def _check_distributed_weightage(self):
        for record in self:
            if record.category == 'department':
                available = record.template_id.potential_available_dept
                current = record.template_id.potential_dept_distributed
            elif record.category == 'role':
                available = record.template_id.potential_available_role
                current = record.template_id.potential_role_distributed
            else:  # common
                available = record.template_id.potential_available_common
                current = record.template_id.potential_common_distributed

            if current > available:
                raise ValidationError(_('Total distributed weightage cannot exceed available weightage of %s%%') % available)


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
    common_weightage = fields.Float('Common Weightage (%)')

    @api.constrains('department_weightage', 'role_weightage', 'common_weightage')
    def _check_weightage_limits(self):
        for record in self:
            # Get available weightages
            available_dept = record.template_id.performance_split if record.type == 'performance' else record.template_id.potential_split
            available_role = record.template_id.role_weightage
            available_common = record.template_id.common_weightage

            # Get total allocated for each type
            domain = [
                ('template_id', '=', record.template_id.id),
                ('type', '=', record.type),
                ('id', '!=', record.id)
            ]
            other_records = self.search(domain)
            total_dept = sum(other_records.mapped('department_weightage')) + record.department_weightage
            total_role = sum(other_records.mapped('role_weightage')) + record.role_weightage
            total_common = sum(other_records.mapped('common_weightage')) + record.common_weightage

            if total_dept > available_dept:
                raise ValidationError(_('Total department weightage cannot exceed %s%%') % available_dept)
            if total_role > available_role:
                raise ValidationError(_('Total role weightage cannot exceed %s%%') % available_role)
            if total_common > available_common:
                raise ValidationError(_('Total common weightage cannot exceed %s%%') % available_common)
            