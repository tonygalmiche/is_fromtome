# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning
import datetime


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    is_commande_soldee = fields.Boolean(string=u'Commande soldée', default=False, copy=False, help=u"Cocher cette case pour indiquer qu'aucune nouvelle livraison n'est prévue sur celle-ci")


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    is_sale_order_line_id = fields.Many2one('sale.order.line', string=u'Ligne commande client', index=True)


