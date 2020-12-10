# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    is_export_compta_id = fields.Many2one('is.export.compta', 'Folio', copy=False)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    is_export_compta_id = fields.Many2one('is.export.compta', 'Folio', copy=False)


