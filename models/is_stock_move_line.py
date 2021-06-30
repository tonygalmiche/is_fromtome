# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools.sql import drop_view_if_exists
from datetime import timedelta


class is_stock_move_line(models.Model):
    _name='is.stock.move.line'
    _description='is.stock.move.line'
    _order='product_id'
    _auto = False


    @api.depends('status_move')
    def _compute_creer_fnc_vsb(self):
        for obj in self:
            vsb = True
            fncs=self.env['is.fnc'].search([('move_line_id', '=', obj.move_line_id.id)])
            if len(fncs)>0:
                vsb=False
            obj.creer_fnc_vsb=vsb


    company_id      = fields.Many2one('res.company', 'Société')
    picking_id      = fields.Many2one('stock.picking', 'Picking')
    picking_type_id = fields.Many2one('stock.picking.type', 'Type')
    partner_id      = fields.Many2one('res.partner', 'Partenaire')
    product_id      = fields.Many2one('product.product', "Article")
    product_tmpl_id = fields.Many2one('product.template', "Modèle d'article")
    move_id         = fields.Many2one('stock.move', 'Mouvement de stock')
    move_line_id    = fields.Many2one('stock.move.line', 'Ligne de mouvement de stock')
    lot_id          = fields.Many2one('stock.production.lot', 'Lot')
    life_use_date   = fields.Datetime('DLC/DDM')
    product_uom_id  = fields.Many2one('uom.uom', 'Unité')
    qty_done        = fields.Float('Qt')
    weight          = fields.Char('Poids')
    status_move     = fields.Selection(string='Statut', selection=[('receptionne', 'Réceptionné'),('manquant', 'Manquant'), ('abime', 'Abimé'), ('autre', 'Autre')])
    creer_fnc_vsb   = fields.Boolean(string='Créer FNC visibility', compute='_compute_creer_fnc_vsb', readonly=True, store=False)


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
                    l.id move_line_id,
                    l.lot_id,
                    l.life_use_date,
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


    @api.multi
    def creer_fnc_action(self):
        for obj in self:
            res=obj.move_line_id.creer_fnc_action()
            return res


    @api.multi
    def acces_fnc_action(self):
        for obj in self:
            res=obj.move_line_id.acces_fnc_action()
            return res
