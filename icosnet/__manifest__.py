
{
    "name": "Icosnet",
    "version": "17.0.1.0.1",
    "category": "Customer Relationship Management",
    "license": "LGPL-3",
    "summary": "odoo custom changes for icosnet",
    "author": "Finoutsource ",
    "website": "https://finoutsource.dz",
    "depends": ['base','account','crm', 'product','stock', 'documents', 'contacts','project','sale_project','sale_subscription'],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/ir_sequence_data.xml",
        "data/product_data.xml",
        "data/mail_activity_type_data.xml",
        "data/ir_cron.xml",

        "wizard/trial_wizard_view.xml",
        "wizard/technical_attributes_wizard_view.xml",

        "views/crm_lead_views.xml",
        "views/configuration.xml",
        "views/crm_lead_line_views.xml",
        "views/partner_view.xml",
        "views/product_template.xml",
        "views/sale_order_views.xml",
        "views/sale_subscription_order_views.xml",
        "views/technical_attribute_common_views.xml",
        "views/report_sale.xml",
        "views/res_country_city.xml",
        "views/res_company_views.xml",
        "views/project_task.xml",
    ],
    
    "installable": True,
    "auto_install": False,
    'assets': {
     
        'web.assets_backend': [
            'icosnet/static/src/js/customSelection.js',

        ]},
}
