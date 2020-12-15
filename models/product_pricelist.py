# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    is_augmentation = fields.Float("Pourcentage d'augmentation à appliquer", digits=(16, 2))
 

    def appliquer_augmentation_action(self):
        for obj in self:
            for item in obj.item_ids:
                price = item.fixed_price + item.fixed_price*obj.is_augmentation/100
                item.fixed_price = price
            obj.is_augmentation=0
