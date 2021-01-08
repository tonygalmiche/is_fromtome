# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'


    def _compute_is_alerte(self):
        for obj in self:
            alerte=''
            for line in obj.invoice_line_ids:
                if line.price_unit==0:
                    alerte = "Prix facturé à 0"
                if line.price_unit>=9999:
                    alerte = "Prix facturé > 9999"
            obj.is_alerte=alerte

    is_export_compta_id = fields.Many2one('is.export.compta', 'Folio', copy=False)
    is_alerte = fields.Text('Alerte', copy=False, compute=_compute_is_alerte)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    is_export_compta_id = fields.Many2one('is.export.compta', 'Folio', copy=False)
