# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import codecs
import unicodedata
import base64
import datetime
from odoo.exceptions import Warning
from math import *


class IsCommandeFromtomeLigne(models.Model):
    _name = 'is.commande.fromtome.ligne'
    _description = u"Commande fromtome Lignes"
    _order='sequence,id'

    commande_id      = fields.Many2one('is.commande.fromtome', u'Commande Fromtome', required=True, ondelete='cascade')
    sequence         = fields.Integer(u"Ordre")
    product_id       = fields.Many2one('product.product', u'Article')
    uom_id           = fields.Many2one('uom.uom', u"Unité de stock")
    uom_po_id        = fields.Many2one('uom.uom', u"Unité d'achat")
    factor_inv       = fields.Float(u"Multiple de", digits=(14,4))
    sale_qty         = fields.Float(u"Qt commande client"          , digits=(14,4))
    purchase_qty     = fields.Float(u"Qt Fromtome déja en commande", digits=(14,4))
    product_qty      = fields.Float(u"Qt Fromtome à commander"     , digits=(14,4))

    stock            = fields.Float(u"Stock", digits=(14,2))
    stock_mini       = fields.Float(u"Stock mini", digits=(14,2))
    order_line_id    = fields.Many2one('purchase.order.line', u'Ligne commande fournisseur')





class IsCommandeFromtome(models.Model):
    _name = 'is.commande.fromtome'
    _description = u"Commande fromtome"
    _order='name desc'

    name       = fields.Char(u"N°", readonly=True)
    partner_id = fields.Many2one('res.partner', u'Fournisseur', required=True)
    stock_mini = fields.Boolean(u"Stock mini", default=True, help=u"Si cette case est cochée, il faut tenir compte du stock mini")
    order_id   = fields.Many2one('purchase.order', u'Commande Fromtome')
    ligne_ids  = fields.One2many('is.commande.fromtome.ligne', 'commande_id', u'Lignes')


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('is.commande.fromtome')
        res = super(IsCommandeFromtome, self).create(vals)
        return res


    @api.multi
    def calcul_besoins_action(self):
        cr,uid,context = self.env.args
        for obj in self:

            if obj.order_id and obj.order_id.state!='draft':
                raise Warning(u"La commande Fromtome associée est déjà validée. Le calcul n'est pas autorisé !")

            obj.ligne_ids.unlink()

            #** Création commande fournisseur **********************************
            if obj.order_id:
                order=obj.order_id
            else:
                vals={
                    'partner_id'  : obj.partner_id.id,
                }
                order=self.env['purchase.order'].create(vals)
                obj.order_id=order.id
            if order:
                order.onchange_partner_id()
            order.order_line.unlink()
            now = datetime.date.today()
            products = self.env['product.product'].search([('sale_ok','=',True)],order='name')
            sequence=0
            for product in products:
                if product.default_code:

                    #** Commande client ****************************************
                    sql="""
                        SELECT  
                            pt.default_code,
                            sol.product_id,
                            sum(sol.product_uom_qty-sol.qty_delivered)
                        FROM sale_order so inner join sale_order_line sol on so.id=sol.order_id
                                           inner join product_product pp on sol.product_id=pp.id
                                           inner join product_template pt on pp.product_tmpl_id=pt.id
                        WHERE 
                            so.state in ('draft','send','sale') and
                            so.delivery_date>='2020-10-01' and
                            sol.product_id="""+str(product.id)+"""
                        GROUP BY pt.default_code,sol.product_id
                        ORDER BY pt.default_code,sol.product_id
                    """
                    cr.execute(sql)
                    sale_qty = 0
                    for row in cr.fetchall():
                        sale_qty = row[2]
                    #***********************************************************

                    #** Commande Fromtome ***********************************
                    sql="""
                        SELECT  
                            pt.default_code,
                            pol.product_id,
                            pol.product_qty,
                            (select sum(product_uom_qty) from stock_move sm where sm.purchase_line_id=pol.id and state='done')
                        FROM purchase_order po inner join purchase_order_line pol on po.id=pol.order_id
                                           inner join product_product pp on pol.product_id=pp.id
                                           inner join product_template pt on pp.product_tmpl_id=pt.id
                        WHERE 
                            po.state not in ('done','cancel') and
                            po.date_planned>='2020-10-01' and
                            pol.product_id="""+str(product.id)+""" and
                            pol.qty_received<pol.product_qty and
                            po.is_commande_soldee='f'
                    """
                    cr.execute(sql)
                    purchase_qty = 0
                    for row in cr.fetchall():
                        purchase_qty += row[2]-(row[3] or 0)
                    #***********************************************************


                    stock_mini=0
                    if obj.stock_mini==True:
                        stock_mini = product.is_stock_mini
                    stock = product.qty_available
                    product_qty = sale_qty - stock + stock_mini - purchase_qty
                    factor_inv = product.uom_po_id.factor_inv
                    if factor_inv>0:
                        product_qty = factor_inv*ceil(product_qty/factor_inv)
                    if product_qty>0:
                        sequence+=1
                        vals={
                            'order_id'    : order.id,
                            'sequence'    : sequence,
                            'product_id'  : product.id,
                            'name'        : product.name,
                            'product_qty' : product_qty,
                            'product_uom' : product.uom_po_id.id,
                            'date_planned': str(now)+' 08:00:00',
                            'price_unit'  : 0,
                        }
                        order_line=self.env['purchase.order.line'].create(vals)
                        order_line.onchange_product_id()
                        order_line.product_qty = product_qty
                        vals={
                            'commande_id'  : obj.id,
                            'sequence'     : sequence,
                            'product_id'   : product.id,
                            'uom_po_id'    : product.uom_po_id.id,
                            'factor_inv'   : factor_inv,
                            'uom_id'       : product.uom_id.id,
                            'sale_qty'     : sale_qty,
                            'purchase_qty' : purchase_qty,
                            'product_qty'  : product_qty,
                            'stock'        : product.qty_available,
                            'stock_mini'   : stock_mini,
                            'order_line_id': order_line.id,
                        }
                        ligne=self.env['is.commande.fromtome.ligne'].create(vals)






