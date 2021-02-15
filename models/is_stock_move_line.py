# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools.sql import drop_view_if_exists
from datetime import timedelta


class is_stock_move_line(models.Model):
    _name='is.stock.move.line'
    _order='product_id'
    _auto = False

    company_id      = fields.Many2one('res.company', 'Société')
    picking_id      = fields.Many2one('stock.picking', 'Picking')
    picking_type_id = fields.Many2one('stock.picking.type', 'Type')
    partner_id      = fields.Many2one('res.partner', 'Partenaire')
    product_id      = fields.Many2one('product.product', "Article")
    product_tmpl_id = fields.Many2one('product.template', "Modèle d'article")
    move_id         = fields.Many2one('stock.move', 'Mouvement de stock')
    lot_id          = fields.Many2one('stock.production.lot', 'Lot')
    product_uom_id  = fields.Many2one('uom.uom', 'Unité')
    qty_done        = fields.Float('Qt')
    weight          = fields.Char('Poids')
    status_move     = fields.Char('Statut')


    def init(self):
        drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute("""
            CREATE OR REPLACE view is_stock_move_line AS (
                select 
                    l.id,
                    pt.company_id,
                    l.picking_id,
                    p.picking_type_id,
                    m.partner_id,
                    l.product_id,
                    pp.product_tmpl_id,
                    l.move_id,
                    l.lot_id,
                    l.product_uom_id,
                    l.qty_done,
                    l.weight,
                    l.status_move
                from stock_move_line l join product_product pp on l.product_id=pp.id 
                                       join product_template pt on pp.product_tmpl_id=pt.id
                                       join stock_move m on l.move_id=m.id
                                       join stock_picking p on l.picking_id=p.id
            )
        """)
