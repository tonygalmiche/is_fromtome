# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning
import datetime


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    is_commande_soldee = fields.Boolean(string=u'Commande soldée', default=False, copy=False, help=u"Cocher cette case pour indiquer qu'aucune nouvelle livraison n'est prévue sur celle-ci")


    @api.multi
    def creer_commande_fromtome_action(self):
        for obj in self:
            vals={
                'company_id': 1,
                'partner_id': 3779,
            }
            order=self.env['sale.order'].sudo().create(vals)
            if order:
                for line in obj.order_line:
                    default_code =  (line.product_id.default_code or '')[2:]
                    filtre=[
                        ('default_code','=', default_code),
                        ('company_id'  ,'=', 1)
                    ]
                    products=self.env['product.product'].sudo().search(filtre,limit=1)
                    for product in products:
                        vals={
                            'sequence'  : line.sequence,
                            'product_id': product.id,
                            'name'      : product.name,
                            'product_uom_qty': line.product_qty,
                            'order_id'       : order.id,
                        }
                        res=self.env['sale.order.line'].sudo().create(vals)


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    is_sale_order_line_id = fields.Many2one('sale.order.line', string=u'Ligne commande client', index=True)



