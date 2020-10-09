# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning
import datetime

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def creer_commande_fournisseur_action(self):
        for obj in self:
            if not obj.delivery_date:
                raise Warning(u"Le champ 'Date Livraison' n'est pas renseigné !")
            if not len(obj.order_line):
                raise Warning(u"Il n'y a aucune ligne de commandes à traiter !")

            now = datetime.date.today()
            print(obj)
            for line in obj.order_line:

                suppliers=self.env['product.supplierinfo'].search([('product_tmpl_id', '=', line.product_id.product_tmpl_id.id)])
                print(line.product_id,line.product_id.seller_ids,suppliers)
                partner_id=False
                supplierinfo=False
                for s in suppliers:
                    print(s.sequence,s.name.id,s.date_start,type(s.date_end))
                    if now>=s.date_start and now<= s.date_end:
                        supplierinfo=s
                        #partner_id=s.name.id
                        break

                if supplierinfo:
                    partner_id = supplierinfo.name.id
                    print('partner_id =',partner_id,supplierinfo,supplierinfo.price)

                    delivery_date = str(obj.delivery_date)[:10]
                    date_planned  = delivery_date+' 08:00:00'

                    filtre=[
                        ('partner_id'  ,'='   , partner_id),
                        ('state'       ,'='   , 'draft'),
                        ('date_planned','>=', delivery_date+' 00:00:00'),
                        ('date_planned','<=', delivery_date+' 23:59:59'),
                    ]

                    print(filtre)
                    orders=self.env['purchase.order'].search(filtre,limit=1)
                    if orders:
                        order=orders[0]
                    else:
                        vals={
                            'partner_id'  : partner_id,
                        }
                        order=self.env['purchase.order'].create(vals)
                        if order:
                            order.onchange_partner_id()
                            #order.date_planned = date_planned

                    print('order =',order)

                    #** Création des lignes ************************************
                    filtre=[
                        ('order_id'  ,'='   , order.id),
                        ('is_sale_order_line_id','=',line.id),
                    ]
                    order_lines=self.env['purchase.order.line'].search(filtre)
                    print('order_lines =',order_lines)
                    if not order_lines:
                        if order:
                            vals={
                                'order_id'    : order.id,
                                'product_id'  : line.product_id.id,
                                'name'        : line.name,
                                'product_qty' : line.product_uom_qty,
                                'product_uom' : line.product_uom.id,
                                'date_planned': date_planned,
                                'price_unit'  : line.price_unit,
                                'is_sale_order_line_id': line.id,
                            }
                            print('vals =',vals)
                            order_line=self.env['purchase.order.line'].create(vals)
                            order_line.onchange_product_id()
                            order_line.product_qty = line.product_uom_qty
                            print('order_line =',order_line)
                    #***********************************************************

