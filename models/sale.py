# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning
import datetime


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends('product_id')
    def _compute_purchase_order_line_id(self):
        for obj in self:
            filtre=[
                ('is_sale_order_line_id','=',obj.id),
            ]
            order_lines=self.env['purchase.order.line'].search(filtre)
            order_id = False
            for line in order_lines:
                if line.order_id.state!='cancel':
                    order_id=line.id
                    break
            obj.is_purchase_order_line_id = order_id

    is_purchase_order_line_id = fields.Many2one('purchase.order.line', string=u'Ligne commande fournisseur', compute='_compute_purchase_order_line_id', readonly=True, store=False)

    @api.multi
    def acceder_commande_fournisseur(self, vals):
        for obj in self:
            res= {
                'name': 'Ligne commande fournisseur',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 'purchase.order.line',
                'type': 'ir.actions.act_window',
                'domain': [
                    ('is_sale_order_line_id','=',obj.id),
                    ('state','!=','cancel'),
                ],
            }
            return res


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends('order_line')
    def _compute_is_creer_commande_fournisseur_vsb(self):
        for obj in self:
            vsb = False
            for line in obj.order_line:
                if not line.is_purchase_order_line_id.id:
                    print(line.is_purchase_order_line_id)
                    vsb=True
                    break
            print('vsb =',vsb)
            obj.is_creer_commande_fournisseur_vsb=vsb

    is_creer_commande_fournisseur_vsb = fields.Boolean(string=u'Créer commande fournisseur', compute='_compute_is_creer_commande_fournisseur_vsb', readonly=True, store=False)

    @api.multi
    def creer_commande_fournisseur_action(self):
        for obj in self:
            if not obj.delivery_date:
                raise Warning(u"Le champ 'Date Livraison' n'est pas renseigné !")
            if not len(obj.order_line):
                raise Warning(u"Il n'y a aucune ligne de commandes à traiter !")
            now = datetime.date.today()
            for line in obj.order_line:
                suppliers=self.env['product.supplierinfo'].search([('product_tmpl_id', '=', line.product_id.product_tmpl_id.id)])
                partner_id=False
                supplierinfo=False
                for s in suppliers:
                    if now>=s.date_start and now<= s.date_end:
                        supplierinfo=s
                        #partner_id=s.name.id
                        break
                if supplierinfo:
                    partner_id = supplierinfo.name.id
                    delivery_date = str(obj.delivery_date)[:10]
                    date_planned  = delivery_date+' 08:00:00'
                    filtre=[
                        ('partner_id'  ,'='   , partner_id),
                        ('state'       ,'='   , 'draft'),
                        ('date_planned','>=', delivery_date+' 00:00:00'),
                        ('date_planned','<=', delivery_date+' 23:59:59'),
                    ]
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

                    #** Création des lignes ************************************
                    filtre=[
                        ('order_id'  ,'='   , order.id),
                        ('is_sale_order_line_id','=',line.id),
                    ]
                    order_lines=self.env['purchase.order.line'].search(filtre)
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
                            order_line=self.env['purchase.order.line'].create(vals)
                            order_line.onchange_product_id()
                            order_line.product_qty = line.product_uom_qty
                    #***********************************************************

