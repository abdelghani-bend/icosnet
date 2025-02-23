# -*- coding: utf-8 -*-
{
    'name': "Icosnet Groups",
    'sequence': 0,
    'author': "FINOUTSOURCE",
    'website': "",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'sale_subscription', 'project', 'icosnet'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv'   
    ],
    'assets': {
        'web.assets_frontend': [
            'icosnet_reports/static/css/custom_style.css',
        ],  
    },
    'application': True,
    'license': 'LGPL-3',
}
