# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_stock_mini = fields.Float("Stock mini", digits=(14,4))

