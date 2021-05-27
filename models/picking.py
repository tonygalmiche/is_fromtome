# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, api, models, _
import time
from datetime import datetime
from dateutil.parser import parse
import dateparser
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.float_utils import float_compare, float_is_zero
from datetime import datetime
from datetime import timedelta

import logging


class Picking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'barcodes.barcode_events_mixin']


    @api.onchange('move_ids_without_package')
    def _compute_is_alerte(self):
        for obj in self:
            obj.is_alerte=str(len(obj.move_ids_without_package))
            alerte=[]
            for line in obj.move_ids_without_package:
                if line.is_alerte:
                    alerte.append(line.is_alerte)
            if len(alerte)>0:
                alerte='\n'.join(alerte)
            else:
                alerte=False
            obj.is_alerte=alerte


    is_alerte = fields.Text('Alerte', copy=False, compute=_compute_is_alerte)



    def _add_product(self, product, barcode, qty=1.0):


        print("##### barcode,product,qty = ",barcode,product,qty)



        #if product:
        #    qty=product.uom_id.factor_inv or 1

        #print("## qty=",qty)


        line = self.move_ids_without_package.filtered(lambda r: r.product_id.id == product.id)
        if line.move_line_ids:
            line.move_line_ids[0].write({'weight_uom_id': line.product_id.weight_uom_id.id})

        if not barcode or str(barcode)[:2] in ("01","02"):
            if line.show_details_visible:
                # message = _('For %s it is necessary to specify some details.') % (product.name)
                # self.env.user.notify_warning(message=message)
                line.is_quantity_done_editable = True
            if line:
                if line.reserved_availability >= line.quantity_done+qty:
                    if line.is_colis:
                        line.move_line_ids[0].qty_done += qty
                    line.move_line_ids[0].split_qty()



                    #line.quantity_done += qty
                    message = _("La quantité de %s est %s ") % (product.name, line.quantity_done)
                    #raise UserError(message)
                    self.env.user.notify_info(message=message)
                else:
                    message = 'La quantité réservée de '+str(line.reserved_availability)+' est déja atteinte !'
                    raise UserError(message)
                    self.env.user.notify_warning(message=message)
            else:
                if self.state == 'draft':
                    vals = {
                        'product_id': product.id,
                        'product_uom': product.uom_id.id,
                        # 'product_uom_qty':1,
                        # 'ordered_qty':1,
                        'quantity_done': 1,
                        'date_expected': fields.Datetime.now(),
                        'location_id': self.location_id.id,
                        'location_dest_id': self.location_dest_id.id,
                        'state': 'draft',
                    }


                    #print("## vals =",vals)


                    line = self.move_lines.new(vals)
                    line.onchange_product_id()
                    self.move_lines += line

                else:
                    message = _('%s n existe pas !') %  product.name
                    self.env.user.notify_danger(message=message)
        else:
            code = str(barcode)[2:]
            n=len(line.move_line_ids)-1
            if n>0:
                if str(barcode)[:2] in ("10"):


                    #print("###### barcode = ",n,barcode)


                    # Modif faite le 21/05/2021 pour mettre la quantité sur les articles de type Pièce
                    if product:
                        if product.uom_id.category_id.name=="Pièce":
                            qty=product.uom_id.factor_inv or 1
                            if qty <1:
                                qty=1


                            #print("###### qty = ",n,barcode,qty)


                            line.move_line_ids[n].write({'weight': qty})

                    #print("######  weight 1 =",line.move_line_ids[n].weight)


                    line.move_line_ids[n].write({'lot_name' : code} )
                    lot = self.env['stock.production.lot'].search([('name','=',code)],limit=1)
                    if not lot:
                        lot = self.env['stock.production.lot'].create(
                            {'name': code, 'product_id': product.id}
                        )
                        message = _('lot créé  %s') % (lot.name)
                        self.env.user.notify_info(message=message)

                    line.move_line_ids[n].write({'lot_id': lot.id})



                    #print("######  weight 2 =",line.move_line_ids[n].weight)


                    message = _('lot numéro  %s') % (lot.name)
                    self.env.user.notify_info(message=message)

                elif str(barcode)[:2] in ("15"):
                    # date_due = dateparser.parse(code, date_formats=['%y%m%d'])
                    # contrat_date_obj = self.env['contrat.date.client'].search([('partner_id','=',self.partner_id.id),('product_id','=',self.product_id.id)],limit=1)
                    # contrat_date = datetime.now() + timedelta(days=contrat_date_obj.name)
                    # print('-date duee---',date_due)
                    # print('-obj contrat date---',contrat_date_obj)
                    # print('contrat date----',contrat_date)
                    # if contrat_date_obj and contrat_date.date() > date_due.date():
                    #     print('---- okkk pass date')
                    # else:
                    #     print('-- no pass date')

                    date_due = dateparser.parse(code, date_formats=['%y%m%d'])

                    #print("## barcode,date_due = ",n,barcode,date_due)

                    contrat_date_obj = self.env['contrat.date.client'].search(
                        [('partner_id', '=', self.partner_id.id),
                         ('product_id', '=', product.product_tmpl_id.id)], limit=1)
                    contrat_date = datetime.now() + timedelta(days=contrat_date_obj.name)
                    if contrat_date_obj and contrat_date.date() > date_due.date():
                        raise UserError(_('Verifiez Contrat date du client !'))
                    elif date_due and date_due.date() < datetime.now().date():
                        raise UserError(_('Produit expiré !'))
                    elif date_due and date_due.date() == datetime.now().date():
                        raise UserError(_('Vérifiez date expiration produit !'))

                    line.move_line_ids[n].write({"life_use_date": date_due} )
                    #line.move_line_ids[n].lot_id.write({"use_date": date_due})



                elif str(barcode)[:2] in ("17"):
                    line.move_line_ids[n].write({"life_use_date" : dateparser.parse(code, date_formats=['%y%m%d'])} )
                    #line.move_line_ids[n].lot_id.write({"life_date": dateparser.parse(code, date_formats=['%y%m%d'])})


                elif str(barcode)[:2] in ("31"):
                    decimal = int(str(barcode)[3])
                    code = float(str(barcode)[4:-decimal] + '.' + str(barcode)[-decimal:])

                    #print("## barcode,decimal,code = ",n,barcode,decimal,code,line.move_line_ids[n].weight_uom_id.category_id.name)



                    if line.move_line_ids[n].weight_uom_id.category_id.name == "Poids":
                        line.move_line_ids[n].write({'weight': code * line.move_line_ids[n].product_uom_qty, 'product_weight':code * line.move_line_ids[n].product_uom_qty} )
                    else:

                        product_weight = code * line.move_line_ids[n].product_uom_qty

                        #print("## barcode,decimal,code,product_weight = ",n,barcode,decimal,code,product_weight)


                        line.move_line_ids[n].write({'product_weight': product_weight})
                        #line.move_line_ids[n].write({'weight': 123})


                        #line.move_line_ids[n].write({'qty_done': 12})



                        #print("## barcode,move_line_ids = ",line.move_line_ids[n], line.move_line_ids[n].weight)





                    line._cal_move_weight()
                # elif str(barcode)[:2] in ("37"):
                #     line.move_line_ids[n].write({'qty_done':  int(code),'weight':line.move_line_ids[n].product_id.weight * int(code)} )
                #     line.move_line_ids[n].write({'product_uom_qty':  int(code)} )
                #     line.move_line_ids[0].write({'product_uom_qty':  line.move_line_ids[0].product_uom_qty - int(code) + 1} )
                #else:
                #    return True

        return True


    def on_barcode_scanned(self, barcode):
        #print('barcode---',barcode,self.env.user,self)

        if self.state not in ['draft', 'assigned']:
            self.env.user.notify_danger(message=_('Status does not allow scanning') )
            return
        product = self.env['product.product'].search([('barcode', '=', barcode)])

        #print('## TEST 1 barcode,product',barcode,product)



        today = datetime.now().date()
        if not product:
            product_tmpl = self.env['product.supplierinfo'].search([('barcode', '=', barcode),('date_end','>=',today)],limit=1).product_tmpl_id
            product = self.env['product.product'].search([('product_tmpl_id', '=', product_tmpl.id)],limit=1)


        #print('## TEST 2 barcode,product',barcode,product)





        if product:
            message = _('product ean13 yes is  %s') % (product.name)
            self.env.user.notify_info(message=message)
            self._add_product(product,False)

        elif str(barcode)[:2] in ("01","02"):
            pr_barcode =  str(barcode)[2:]
            product = self.env['product.product'].search([('barcode', '=',str(barcode)[2:])])
            if not product:
                product_tmpl = self.env['product.supplierinfo'].search([('barcode', '=', str(barcode)[2:]),('date_end','>=',today)],limit=1).product_tmpl_id
                product = self.env['product.product'].search([('product_tmpl_id', '=', product_tmpl.id)],limit=1)
            if product:
                self._add_product(product, barcode)
                self.barcode_product_id =  product.id


            #print('## TEST 3 barcode,product',barcode,product)




        elif str(barcode)[:2] in ('10','15','17','31','37'):
            self._add_product(self.barcode_product_id, barcode)
        else:
            self.barcode_product_id = False
            self.env.user.notify_danger(message=_('There is no product with barcode %s') % barcode )


    @api.multi
    def button_validate(self):
        self.ensure_one()
        if not self.move_lines and not self.move_line_ids:
            raise UserError(_('Please add some items to move.'))

        # If no lots when needed, raise error
        picking_type = self.picking_type_id
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in
                                 self.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
        no_reserved_quantities = all(
            float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in
            self.move_line_ids)
        if no_reserved_quantities and no_quantities_done:
            print('You cannot validate a transfer if no quantites are reserved nor done. To force the transfer, switch in edit more and encode the done quantities.')
            # raise UserError(_(
            #     'You cannot validate a transfer if no quantites are reserved nor done. To force the transfer, switch in edit more and encode the done quantities.'))

        if picking_type.use_create_lots or picking_type.use_existing_lots:
            lines_to_check = self.move_line_ids
            if not no_quantities_done:
                lines_to_check = lines_to_check.filtered(
                    lambda line: float_compare(line.qty_done, 0,
                                               precision_rounding=line.product_uom_id.rounding)
                )

            for line in lines_to_check:
                product = line.product_id
                if product and product.tracking != 'none':
                    if not line.lot_name and not line.lot_id:
                        print('You need to supply a Lot/Serial number for product  in ean picking module')

                        # raise UserError(
                        #     _('You need to supply a Lot/Serial number for product %s.') % product.display_name)

        if no_quantities_done:
            view = self.env.ref('stock.view_immediate_transfer')
            wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, self.id)]})
            return {
                'name': _('Immediate Transfer?'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.immediate.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }

        if self._get_overprocessed_stock_moves() and not self._context.get('skip_overprocessed_check'):
            view = self.env.ref('stock.view_overprocessed_transfer')
            wiz = self.env['stock.overprocessed.transfer'].create({'picking_id': self.id})
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.overprocessed.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }

        # Check backorder should check for other barcodes
        if self._check_backorder():
            return self.action_generate_backorder_wizard()
        self.action_done()
        return




class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.onchange('qty_done','product_uom_qty')
    def delete_line_qty_zero(self):
        if self.product_uom_qty == 0:
            self.unlink()

    @api.constrains('lot_id', 'product_id')
    def _check_lot_product(self):
        for line in self:
            if line.lot_id and line.product_id != line.lot_id.product_id:
                print('this lot is incompatible with this product .')
                # raise ValidationError(_('This lot %s is incompatible with this product %s' % (
                # line.lot_id.name, line.product_id.display_name)))


class StockQuant(models.Model):
    _inherit = 'stock.quant'
    @api.model
    def _update_reserved_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None,
                                  strict=False):
        """ Increase the reserved quantity, i.e. increase `reserved_quantity` for the set of quants
        sharing the combination of `product_id, location_id` if `strict` is set to False or sharing
        the *exact same characteristics* otherwise. Typically, this method is called when reserving
        a move or updating a reserved move line. When reserving a chained move, the strict flag
        should be enabled (to reserve exactly what was brought). When the move is MTS,it could take
        anything from the stock, so we disable the flag. When editing a move line, we naturally
        enable the flag, to reflect the reservation according to the edition.

        :return: a list of tuples (quant, quantity_reserved) showing on which quant the reservation
            was done and how much the system was able to reserve on it
        """
        self = self.sudo()
        rounding = product_id.uom_id.rounding
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id,
                              strict=strict)
        reserved_quants = []

        if float_compare(quantity, 0, precision_rounding=rounding) > 0:
            # if we want to reserve
            available_quantity = self._get_available_quantity(product_id, location_id, lot_id=lot_id,
                                                              package_id=package_id, owner_id=owner_id, strict=strict)
            # if float_compare(quantity, available_quantity, precision_rounding=rounding) > 0:
            #     raise UserError(_('It is not possible to reserve more products of %s than you have in stock.') % product_id.display_name)
        elif float_compare(quantity, 0, precision_rounding=rounding) < 0:
            # if we want to unreserve
            available_quantity = sum(quants.mapped('reserved_quantity'))
            # if float_compare(abs(quantity), available_quantity, precision_rounding=rounding) > 0:
            #     raise UserError(_('It is not possible to unreserve more products of %s than you have in stock.') % product_id.display_name)
        else:
            return reserved_quants

        for quant in quants:
            if float_compare(quantity, 0, precision_rounding=rounding) > 0:
                max_quantity_on_quant = quant.quantity - quant.reserved_quantity
                if float_compare(max_quantity_on_quant, 0, precision_rounding=rounding) <= 0:
                    continue
                max_quantity_on_quant = min(max_quantity_on_quant, quantity)
                quant.reserved_quantity += max_quantity_on_quant
                reserved_quants.append((quant, max_quantity_on_quant))
                quantity -= max_quantity_on_quant
                available_quantity -= max_quantity_on_quant
            else:
                max_quantity_on_quant = min(quant.reserved_quantity, abs(quantity))
                quant.reserved_quantity -= max_quantity_on_quant
                reserved_quants.append((quant, -max_quantity_on_quant))
                quantity += max_quantity_on_quant
                available_quantity += max_quantity_on_quant

            if float_is_zero(quantity, precision_rounding=rounding) or float_is_zero(available_quantity,
                                                                                     precision_rounding=rounding):
                break
        return reserved_quants

