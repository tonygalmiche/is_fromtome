# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.constrains('barcode','active','product_tmpl_id')
    def _check_barcode_unique(self):
        for obj in self:
            if obj.barcode:
                filtre=[
                    ('barcode', '=' , obj.barcode),
                    ('id'  , '!=', obj.id),
                    ('product_tmpl_id.company_id', '=', obj.product_tmpl_id.company_id.id),
                ]
                products = self.env['product.product'].sudo().search(filtre, limit=1)
                if products:
                    raise Warning("Le code barre doit-être unique !") 

 
class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_stock_mini         = fields.Float("Stock mini", digits=(14,4))
    is_pricelist_item_ids = fields.One2many('product.pricelist.item', 'product_tmpl_id', 'Liste de prix')

