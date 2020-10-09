# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning
import datetime

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    is_sale_order_line_id = fields.Many2one('sale.order.line', string=u'Ligne commande client', index=True)


