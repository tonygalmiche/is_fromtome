# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_date_reception = fields.Date(string=u'Dernière date de réception saisie')



