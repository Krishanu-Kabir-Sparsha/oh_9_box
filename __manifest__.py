{
    'name': 'OH Appraisal 9-Box Grid',
    'version': '1.0',
    'category': 'Human Resources/Appraisals',
    'summary': '9-Box Grid Assessment Framework',
    'description': """
        9-Box Grid Assessment Framework for Employee Evaluation
        - Define performance and potential criteria
        - Configure weightages and assessment parameters
        - Integrate with existing appraisal framework
    """,
    'author': 'Odoo Humans',
    'website': 'https://www.odoohumans.com',
    'depends': [
        'base',
        'hr',
        'mail',
        'web',
        'oh_appraisal',  # Ensure this module is installed first
        'oh_appraisal_ext'
    ],
    'data': [
        'security/ninebox_security.xml',  # Add security groups first
        'security/ir.model.access.csv',
        'views/ninebox_template_views.xml',
        'views/menu_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}