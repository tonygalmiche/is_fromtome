# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class IsFNC(models.Model):
    _name = 'is.fnc'
    _description = "Fiche de non-conformité Client / Fournisseur"
    _order = 'name desc'

    name             = fields.Char(u"N°FNC", readonly=True)
    company_id       = fields.Many2one('res.company', 'Société'    , required=True, default=lambda self: self.env.user.company_id.id, readonly=True)
    emetteur_id      = fields.Many2one('res.users'   , 'Émetteur'  , required=True, default=lambda self: self.env.user.id, readonly=True)
    date_creation    = fields.Date("Date de création"              , required=True, default=lambda *a: fields.Date.today(), readonly=True)
    move_line_id     = fields.Many2one('stock.move.line', 'Ligne de mouvement')
    product_id       = fields.Many2one('product.product', 'Produit', required=True)
    lot_id           = fields.Many2one('stock.production.lot', 'N° de lot')
    dlc_ddm          = fields.Date('DLC/DDM')
    status_move      = fields.Selection(string='Statut', selection=[('receptionne', 'Réceptionné'),('manquant', 'Manquant'), ('abime', 'Abimé'), ('autre', 'Autre')], required=True)
    description      = fields.Text('Desciption de la non-conformité')
    cause            = fields.Text('Causes')
    action_immediate = fields.Text('Action immédiate')
    state            = fields.Selection([
            ('en_cours', 'En cours'),
            ('solde'   , 'Soldé'),
        ], 'État', default="en_cours")


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('is.fnc')
        res = super(IsFNC, self).create(vals)
        return res


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.depends('status_move')
    def _compute_is_creer_fnc_vsb(self):
        for obj in self:
            vsb = True
            obj.is_creer_fnc_vsb=vsb

    @api.depends('status_move')
    def _compute_is_acces_fnc_vsb(self):
        for obj in self:
            vsb = True
            obj.is_acces_fnc_vsb=vsb

    is_creer_fnc_vsb = fields.Boolean(string='Créer FNC visibility', compute='_compute_is_creer_fnc_vsb', readonly=True, store=False)
    is_acces_fnc_vsb = fields.Boolean(string='Créer FNC visibility', compute='_compute_is_acces_fnc_vsb', readonly=True, store=False)

    @api.multi
    def creer_fnc_action(self):
        for obj in self:

            fncs=self.env['is.fnc'].search([('move_line_id', '=', obj.id)])

            print(fncs)
            fnc_id=False
            for fnc in fncs:
                fnc_id=fnc.id

            if not fnc_id:
                vals={
                    'move_line_id': obj.id,
                    'product_id'  : obj.move_id.product_id.id,
                    'lot_id'      : obj.lot_id.id,
                    'dlc_ddm'     : obj.life_use_date,
                    'status_move' : obj.status_move,
                }
                fnc=self.env['is.fnc'].create(vals)
                fnc_id = fnc.id
            res= {
                'name': 'FNC',
                'view_mode': 'form,tree',
                'view_type': 'form',
                'res_model': 'is.fnc',
                'type': 'ir.actions.act_window',
                'res_id':fnc_id,
            }
            return res


    @api.multi
    def acces_fnc_action(self):
        for obj in self:
            print(obj)
 
