# -*- coding: utf-8 -*-
{
    'name'     : 'InfoSaône - Module Odoo 12 pour Fromtome',
    'version'  : '0.1',
    'author'   : 'InfoSaône',
    'category' : 'InfoSaône',
    'description': """
InfoSaône - Module Odoo 12 pour Fromtome 
===================================================
""",
    'maintainer' : 'InfoSaône',
    'website'    : 'http://www.infosaone.com',
    'depends'    : [
        'base',
        'sale',
        'account',
    ],
    'data' : [
        'security/ir.model.access.csv',
        'views/sale_views.xml',
        'views/purchase_views.xml',
        'views/is_export_compta_views.xml',
    ],
    'installable': True,
    'application': True,
}
