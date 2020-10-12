# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class IsExportComptaLigne(models.Model):
    _name = 'is.export.compta.ligne'
    _description = u"Export Compta Lignes"
    _order='ligne,id'

    export_compta_id = fields.Many2one('is.export.compta', u'Export Compta', required=True, ondelete='cascade')
    ligne            = fields.Integer(u"Ligne")
    journal_code     = fields.Char(u"JournalCode")
    journal_lib      = fields.Char(u"JournalLib")
    ecriture_num     = fields.Char(u"EcritureNum")
    ecriture_date    = fields.Date(u"EcritureDate")
    compte_num       = fields.Char(u"CompteNum")
    compte_lib       = fields.Char(u"CompteLib")
    comp_aux_num     = fields.Char(u"CompAuxNum")
    comp_aux_lib     = fields.Char(u"CompAuxLib")
    piece_ref        = fields.Char(u"PieceRef")
    piece_date       = fields.Date(u"PieceDate")
    ecriture_lib     = fields.Char(u"EcritureLib")
    debit            = fields.Float(u"Debit" , digits=(14,2))
    credit           = fields.Float(u"Credit", digits=(14,2))


class IsExportCompta(models.Model):
    _name = 'is.export.compta'
    _description = "Export Compta"
    _order = 'name desc'

    name       = fields.Char(u"N°Folio", readonly=True)
    date_fin   = fields.Date(u"Date de fin"  , required=True)
    ligne_ids  = fields.One2many('is.export.compta.ligne', 'export_compta_id', u'Lignes')


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('is.export.compta')
        res = super(IsExportCompta, self).create(vals)
        return res


    @api.multi
    def export_compta_action(self):
        cr,uid,context = self.env.args
        for obj in self:
            print(obj)
            obj.ligne_ids.unlink()

            sql="""
                SELECT  
                    aj.code,
                    am.name,
                    am.date,
                    aa.code,
                    aa.name,
                    ai.number,
                    ai.date,
                    aml.name,
                    aml.debit,
                    aml.credit
                FROM account_move_line aml inner join account_move am                on aml.move_id=am.id
                                           left outer join account_invoice ai        on aml.move_id=ai.move_id
                                           inner join account_account aa             on aml.account_id=aa.id
                                           left outer join res_partner rp            on aml.partner_id=rp.id
                                           inner join account_journal aj             on aml.journal_id=aj.id
                WHERE 
                    aml.date>='2020-10-01' and
                    aml.date<='"""+str(obj.date_fin)+"""' 
                ORDER BY aml.date
            """
            cr.execute(sql)
            ct=0
            for row in cr.fetchall():
                print(row)
                ct=ct+1
                vals={
                    'export_compta_id': obj.id,
                    'ligne'           : ct,
                    'journal_code'           : row[0],
                    'ecriture_num'           : row[1],
                    'ecriture_date'          : row[2],
                    'compte_num'             : row[3],
                    'compte_lib'             : row[4],
                    'piece_ref'              : row[5],
                    'piece_date'             : row[6],
                    'ecriture_lib'           : row[7],
                    'debit'                  : row[8],
                    'credit'                 : row[9],

                }
                self.env['is.export.compta.ligne'].create(vals)

#    comp_aux_num     = fields.Char(u"CompAuxNum")
#    comp_aux_lib     = fields.Char(u"CompAuxLib")

#    piece_ref        = fields.Char(u"PieceRef")
#    piece_date       = fields.Date(u"PieceDate")
#    ecriture_lib     = fields.Char(u"EcritureLib")
#    debit            = fields.Float(u"Debit" , digits=(14,2))
#    credit           = fields.Float(u"Credit", digits=(14,2))



