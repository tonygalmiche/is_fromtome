# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import codecs
import unicodedata
import base64
from datetime import datetime
import subprocess

class IsImprimerEtiquetteGS1(models.Model):
    _name = 'is.imprimer.etiquette.gs1'
    _description = u"Imprimer des éiquettes GS1"
    _order='id desc'

    code_gs1   = fields.Text("Code GS1")
    code_ean   = fields.Char("Code EAN (01)")
    product_id = fields.Many2one('product.product', 'Article', required=True)
    lot        = fields.Char("Lot (10)", required=True)
    dlc        = fields.Date("DLC (17)")
    dluo       = fields.Date("DDM (15)")
    nb_pieces  = fields.Integer("Nb pièces (37)", required=True, default=1)
    poids      = fields.Float("Poids (31xx)"    , required=True, digits=(14,4))
    qt_imprime = fields.Integer("Quantité à Imprimer", required=True, default=1)


    def str2date(self,txt):
        try:
            dt = datetime.strptime(txt, "%y%m%d").strftime("%Y-%m-%d")
        except ValueError:
            dt = False
        return dt


    @api.onchange('code_gs1','product_id')
    def code_gs1_change(self):
        if self.code_gs1:
            lines = self.code_gs1.strip().split('\n')
            if len(lines)==1:
                self.code_ean = lines[0].strip()
            if len(lines)>1:
                for line in lines:
                    line=line.strip()
                    if line:
                        if line[:2] in ['00','01','02']:
                            code_ean = line[2:]
                            self.code_ean = code_ean
                        if line[:2]=='10':
                            self.lot = line[2:]
    
                        if line[:2]=='15':
                            dluo = self.str2date(line[2:])
                            self.dluo = dluo

                        if line[:2]=='17':
                            dlc = self.str2date(line[2:])
                            self.dlc = dlc

                        if line[:2]=='31':
                            nb_decimales = float(line[3:4])
                            if nb_decimales>0:
                                poids = float(line[4:]) / (10**nb_decimales)
                                self.poids = poids

                        if line[:2]=='37':
                            self.nb_pieces = int(line[2:])
        if self.code_ean:
            products = self.env['product.product'].search([('barcode', '=', self.code_ean)])
            for product in products:
                self.product_id = product.id
        if self.product_id and not self.lot:
            self.lot=self.product_id.default_code+datetime.now().strftime("%j%y")


    @api.multi
    def imprimer_etiquette_action(self):
        for obj in self:
            code_ean = ("00000000000000"+(obj.product_id.barcode or ''))[-14:]
            lot      = ("00000000000000000000"+(obj.lot or ''))[-20:]


            code_gs1 = ">;"
            code_gs1 += ">801"+code_ean
            code_gs1 += ">810"+lot
            if obj.dluo:
                code_gs1+=">815"+obj.dluo.strftime("%y%m%d")
            if obj.dlc:
                code_gs1+=">817"+obj.dlc.strftime("%y%m%d")
            code_gs1 += ">83103"+("000000"+str(int(obj.poids*1000)))[-6:]
            #code_gs1 += ">837"+str(obj.nb_pieces)

            #code_gs1 = ">;>8011234567890123421123456>810>6ABC123>810>6ABC123"

	        #code_gs1=">;> 8011234567890123421123456> 810> 6ABC123"

            code_gs1f = ""
            code_gs1f += "(01)"+code_ean
            code_gs1f += " (10)"+lot
            if obj.dluo:
                code_gs1f+=" (15)"+obj.dluo.strftime("%y%m%d")
            if obj.dlc:
                code_gs1f+=" (17)"+obj.dlc.strftime("%y%m%d")
            code_gs1f += " (3103)"+("000000"+str(int(obj.poids*1000)))[-6:]
            #code_gs1f += " (37)"+str(obj.nb_pieces)

            ZPL="""
^XA
^CI28
^BY2                            ^FX BY = Taille du code barre
^FO0,100                        ^FX Positionnement
^BCN,150,N,N,Y                  ^FX Type de code barre
^FD%s^FS                        ^FX Code barre

^CF0,24                                     ^FX CF0 = Choix de la foncte (font 0) et taille de 30pt
^FO0,280^FD%s^FS                            ^FX Legende du code barre

^CF0,40                                     ^FX CF0 = Choix de la foncte (font 0) et taille de 40pt
^FO0,330^FDArticle : %s^FS                  ^FX Position et texte

^CF0,40                                     ^FX CF0 = Choix de la fonte (font 0) et taille de 30pt
^FO0,380^FD%s^FS                            ^FX Position et texte

^CF0,40                                     ^FX CF0 = Choix de la foncte (font 0) et taille de 40pt
^FO0,430^FDCode EAN (01) : %s^FS            ^FX Position et texte
^FO0,480^FDLot (10) : %s^FS                 ^FX Position et texte
^FO0,580^FDDDM (15) : %s^FS                ^FX Position et texte
^FO0,530^FDDLC (17) : %s^FS                 ^FX Position et texte
^FO0,630^FDPoids (3103) : %s^FS             ^FX Position et texte
^FO0,680^FDNb pièces (37) : %s^FS
^XZ
            """ % (
                code_gs1,
                code_gs1f,
                obj.product_id.default_code,
                obj.product_id.name,
                code_ean,
                lot,
                obj.dluo or '',
                obj.dlc or '',
                obj.poids,
                obj.nb_pieces
            )
            name='etiquette-gs1-zpl'
            dest = '/tmp/'+name
            f = codecs.open(dest,'wb',encoding='utf-8')
            f.write(ZPL)
            f.close()

            cmd = "lpr -P GX430T " + dest
            subprocess.check_call(cmd, shell=True)
