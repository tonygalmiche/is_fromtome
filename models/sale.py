# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning
import datetime

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def creer_commande_fournisseur_action(self):
        for obj in self:
            now = datetime.date.today()
            print(obj)
            for line in obj.order_line:

                suppliers=self.env['product.supplierinfo'].search([('product_tmpl_id', '=', line.product_id.product_tmpl_id.id)])
                print(line.product_id,line.product_id.seller_ids,suppliers)
                partner_id=False
                for s in suppliers:
                    print(s.sequence,s.name.id,s.date_start,type(s.date_end))
                    if now>=s.date_start and now<= s.date_end:
                        partner_id=s.name.id
                        break
                print('partner_id =',partner_id)

                #TODO : 
                #Rechercher si une commande founrisseur existe pour la date indiquée






#            vals={
#                'invoice_id'           : obj.id,
#                'product_id'           : product_id.id,
#                'name'                 : ' ',
#                'price_unit'           : 0,
#                'account_id'           : account_id,
#                'is_dates_intervention': act.dates_intervention,
#                'is_activite_id'       : act.id,
#            }
#            line=self.env['account.invoice.line'].create(vals)

