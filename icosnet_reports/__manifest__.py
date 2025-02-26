# -*- coding: utf-8 -*-
{
    'name': "Icosnet Reports",
    'sequence': 0,
    'author': "FINOUTSOURCE",
    'website': "",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base','sale'],
    'data': [
        'reports/purchase_order.xml',
        'reports/english_quote_report.xml',
        'reports/report.xml',
    ],
    'assets': {
        'web.report_assets_common': [
            'icosnet_reports/static/css/custom_style.css',

        ],
    },
    'application': True,
    'license': 'LGPL-3',
}
