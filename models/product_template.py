# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_stock_mini         = fields.Float("Stock mini", digits=(14,4))
    is_pricelist_item_ids = fields.One2many('product.pricelist.item', 'product_tmpl_id', 'Liste de prix')




#    @api.multi
#    def exporter_article_fromelier_action(self):
#        for obj in self:
#            print(obj)
#            default_code =  'LF'+(obj.default_code or '')
#            filtre=[
#                ('default_code','=', default_code),
#                ('company_id'  ,'=', 2),
#            ]
#            print(filtre)
#            products=self.env['product.product'].sudo().search(filtre,limit=1)
#            print(obj,default_code,products)
#            if len(products)==0:
#                res=obj.sudo().copy()
#                print('res =',res)
#                vals={
#                    'company_id':2,
#                    'default_code':default_code,
#                }
#                res2=obj.sudo().write(vals)
#                print('res2 =',res2)

#            
#            res= {
#                'name': 'Article',
#                'view_mode': 'form',
#                'view_type': 'form',
#                'res_model': 'product.template',
#                'res_id': obj.id,
#                'type': 'ir.actions.act_window',
#            }
#            return res

