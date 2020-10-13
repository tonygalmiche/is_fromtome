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
        'security/ir.model.access.xml',
        'views/sale_views.xml',
        'views/purchase_views.xml',
        'views/is_export_compta_views.xml',
        'views/account_invoice_view.xml',
        'views/stock_move_views.xml',

    ],
    'installable': True,
    'application': True,
}
