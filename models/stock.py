# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning
from datetime import datetime, timedelta


class StockInventory(models.Model):
    _inherit = "stock.inventory"

    @api.multi
    def valorisation_stock_action(self):
        for obj in self:
            dummy, tree_view_id = self.env['ir.model.data'].get_object_reference('is_fromtome', 'is_stock_inventory_line_tree')
            dummy, form_view_id = self.env['ir.model.data'].get_object_reference('is_fromtome', 'is_stock_inventory_line_form')
            return {
                'name': u'Stock valorisé '+obj.name,
                'view_mode': 'tree,form',
                'view_type': 'form',
                'views': [[tree_view_id, "tree"], [form_view_id, "form"]],
                'res_model': 'stock.inventory.line',
                'domain': [
                     ('inventory_id','=',obj.id)
                ],
                'type': 'ir.actions.act_window',
                'limit':1000,
            }


class StockInventoryLine(models.Model):
    _inherit = "stock.inventory.line"


    @api.depends('product_id')
    def compute_is_dernier_prix(self):
        cr,uid,context = self.env.args
        sale_qty = 0
        for obj in self:
            SQL="""
                SELECT ail.price_unit,ai.type,ail.uom_id
                FROM account_invoice_line ail inner join account_invoice ai on ail.invoice_id=ai.id
                WHERE ail.product_id=%s and ail.company_id=%s and ai.state in ('paid','open') and ai.type='in_invoice'
                ORDER BY ail.id desc
                limit 1
            """
            cr.execute(SQL,[obj.product_id.id,obj.inventory_id.company_id.id])
            prix=0
            uom_id = obj.product_uom_id.id
            for row in cr.fetchall():
                prix = row[0]
                uom_id=row[2]
            obj.is_dernier_prix   = prix
            obj.is_stock_valorise = prix*obj.product_qty
            obj.is_uom_facture_id = uom_id


    is_default_code    = fields.Char('Référence interne'           , related='product_id.default_code')
    is_product_name    = fields.Char('Désignation article'         , related='product_id.name')
    is_dernier_prix    = fields.Float("Dernier prix facturé"       , compute=compute_is_dernier_prix, store=False)
    is_stock_valorise  = fields.Float("Stock valorisé"             , compute=compute_is_dernier_prix, store=False)
    is_uom_facture_id  = fields.Many2one('uom.uom', 'Unité facture', compute=compute_is_dernier_prix, store=False)



class StockProductionLot(models.Model):
    _inherit = "stock.production.lot"

    is_article_actif = fields.Boolean('Article actif', related='product_id.active')


    #TODO le 29/05/21 => La suppression de la contrainte ci-dessous ne fonctionne pas => J'a modifié Odoo en dure pour y arriver
    #_sql_constraints = [
    #    ('name_ref_uniq', 'CHECK(1=1)', 'The combination of serial number and product must be unique !'),
    #]
    # def _auto_init(self, cr, context=None):
    #     self._sql_constraints = [
    #         ('serial_no', 'CHECK(1=1)', "Another asset already exists with this serial number!"),
    #     ]
    #     super(StockProductionLot, self)._auto_init(cr, context)
    #@api.model_cr_context
    #def _auto_init(self):
    #    super(StockProductionLot, self)._auto_init()
    #    self._sql_constraints += [
    #        ('name_ref_uniq', 'CHECK(1=1)', 'The combination of serial number and product must be unique !'),
    #    ]
    #    self._add_sql_constraints()


    @api.constrains('name','product_id','is_company_id','active')
    def _check_lot_unique(self):
        for obj in self:
            print(obj)
            # filtre=[
            #     ('name', '=' , obj.name),
            #     ('id'  , '!=', obj.id),
            #     ('product_id'  , '=', obj.product_id.id),
            #     ('is_company_id', '=', obj.is_company_id.id),
            # ]
            # lots = self.env['stock.production.lot'].search(filtre, limit=1)
            # if lots:
            #     raise Warning("Ce lot existe déjà !") 


    @api.depends('product_id')
    def compute_is_company_id(self):
        for obj in self:
            obj.is_company_id=obj.product_id.company_id.id


    is_company_id = fields.Many2one('res.company', 'Société', compute=compute_is_company_id, store=True)
    active        = fields.Boolean("Actif", default=True)


    @api.multi
    def archiver_lot_action_server(self):
        for obj in self:
            try:
                company_id=obj.product_id.company_id.id
            except:
                company_id=False

            if company_id and company_id==self.env.user.company_id.id:
                if obj.product_qty==0:
                    obj.active=False


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.onchange('move_line_ids')
    def _compute_is_alerte(self):
        for obj in self:
            if obj.picking_id:
                alerte=False
                state=obj.picking_id.state
                if state in ['draft', 'cancel', 'waiting', 'confirmed']:
                    alerte=False
                else:
                    if obj.picking_id.scheduled_date:
                        date=obj.picking_id.scheduled_date.date()
                        if state=='assigned' and date<datetime.now().date():
                            date=datetime.now().date()
                        alerte=[]
                        for line in obj.move_line_ids:
                            date_due = line.life_use_date
                            if date_due and date_due.date() < date:
                                alerte.append("Le lot "+str(line.lot_id.name)+" de l'article "+str(obj.product_id.display_name)+" est expiré !")
                            if date_due and date_due.date() ==date:
                                alerte.append("Le lot "+str(line.lot_id.name)+" de l'article "+str(obj.product_id.display_name)+" expire aujourd'hui !")
                            #contrat_date_obj = self.env['contrat.date.client'].search(
                            #    [('partner_id', '=', obj.picking_id.partner_id.id), ('product_id', '=', obj.product_id.product_tmpl_id.id)], limit=1)
                            #contrat_date = date + timedelta(days=contrat_date_obj.name)
                            #if contrat_date and date_due and contrat_date.date() > date_due.date():
                            #    alerte.append("Verifiez le Contrat date du client pour le lot "+line.lot_id.name+" de l'article "+obj.product_id.display_name+" !")
                            #contrat_date_obj = self.env['contrat.date.client'].search(
                            #    [('partner_id', '=', False), ('product_id', '=', obj.product_id.product_tmpl_id.id)], limit=1)
                            #contrat_date = date + timedelta(days=contrat_date_obj.name)
                            #print(obj,obj.picking_id,contrat_date_obj,contrat_date_obj.product_id,contrat_date,contrat_date,date_due.date())
                            #print(contrat_date,date_due)
                            #if contrat_date and date_due and contrat_date > date_due.date():
                            #    alerte.append("Verifiez le Contrat date Fromtome pour le lot "+line.lot_id.name+" de l'article "+obj.product_id.display_name+" !")
                        if len(alerte)>0:
                            alerte='\n'.join(alerte)
                        else:
                            alerte=False
                obj.is_alerte=alerte


    is_alerte = fields.Text('Alerte', copy=False, compute=_compute_is_alerte)
