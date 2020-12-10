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
        'b2c_cheese_base',
    ],
    'data' : [
        'security/res.groups.xml',
        'security/ir.model.access.csv',
        'security/ir.model.access.xml',
        'views/product_views.xml',
        'views/sale_views.xml',
        'views/purchase_views.xml',
        'views/picking_views.xml',
        'views/is_export_compta_views.xml',
        'views/account_invoice_view.xml',
        'views/stock_move_views.xml',
        'views/is_commande_fromtome_views.xml',
        'views/mail_views.xml',
        'views/is_account_invoice_line.xml',
        'views/is_sale_order_line.xml',
        'wizard/mail_compose_message_view.xml',
    ],
    'installable': True,
    'application': True,
}
