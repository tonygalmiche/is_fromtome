# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import codecs
import unicodedata
import base64


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
    invoice_id       = fields.Many2one('account.invoice', u'Facture')
    payment_id       = fields.Many2one('account.payment', u'Paiement')


class IsExportCompta(models.Model):
    _name = 'is.export.compta'
    _description = "Export Compta"
    _order = 'name desc'

    name       = fields.Char(u"N°Folio", readonly=True)
    date_fin   = fields.Date(u"Date de fin"  , required=True)
    escompte   = fields.Boolean(u"Exporter les escomptes", default=True)

    ligne_ids  = fields.One2many('is.export.compta.ligne', 'export_compta_id', u'Lignes')
    file_ids   = fields.Many2many('ir.attachment', 'is_export_compta_attachment_rel', 'doc_id', 'file_id', u'Fichiers')
    company_id = fields.Many2one('res.company', u'Société',required=True,default=lambda self: self.env.user.company_id.id)


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('is.export.compta')
        res = super(IsExportCompta, self).create(vals)
        return res


    @api.multi
    def generer_lignes_action(self):
        cr,uid,context = self.env.args
        for obj in self:
            invoices = self.env['account.invoice'].search([('is_export_compta_id','=',obj.id)])
            for invoice in invoices:
                invoice.is_export_compta_id=False
            obj.ligne_ids.unlink()
            sql="""
                SELECT  
                    aj.name,
                    am.name,
                    am.date,
                    aa.code,
                    aa.name,
                    ai.number,
                    ai.date,
                    aml.name,
                    aml.debit,
                    aml.credit,
                    rp.name,
                    rp.ref,
                    ai.id
                FROM account_move_line aml inner join account_move am                on aml.move_id=am.id
                                           left outer join account_invoice ai        on aml.move_id=ai.move_id
                                           inner join account_account aa             on aml.account_id=aa.id
                                           left outer join res_partner rp            on aml.partner_id=rp.id
                                           inner join account_journal aj             on aml.journal_id=aj.id
                WHERE 
                    aml.date<='"""+str(obj.date_fin)+"""' and 
                    aj.code in ('VE','FACTU','LF/FC','AC') and
                    am.company_id="""+str(self.env.user.company_id.id)+""" and
                    ai.is_export_compta_id is null
                ORDER BY aml.date
            """
            cr.execute(sql)
            ct=0
            for row in cr.fetchall():
                invoice_id = row[12]
                invoices = self.env['account.invoice'].search([('id','=',invoice_id)])
                compte_num = row[3]
                comp_aux_num = ''
                if compte_num[:3] in ['401','411']:
                    comp_aux_num = row[11]
                for invoice in invoices:
                    invoice.is_export_compta_id = obj.id
                    if compte_num[:3]=='411':
                        compte_num = invoice.partner_id.property_account_receivable_id.code
                    if compte_num[:3]=='401':
                        compte_num = invoice.partner_id.property_account_payable_id.code
                ct=ct+1
                vals={
                    'export_compta_id': obj.id,
                    'ligne'           : ct,
                    'journal_code'           : row[0],
                    'ecriture_num'           : row[1],
                    'ecriture_date'          : row[2],
                    'compte_num'             : compte_num,
                    'comp_aux_num'           : comp_aux_num,
                    'piece_ref'              : row[5],
                    'piece_date'             : row[6],
                    'ecriture_lib'           : row[10] or row[7],
                    'debit'                  : row[8],
                    'credit'                 : row[9],
                    'invoice_id'             : invoice_id,
                }
                self.env['is.export.compta.ligne'].create(vals)


            if obj.escompte:
                payments = self.env['account.payment'].search([('is_export_compta_id','=',obj.id)])
                for payment in payments:
                    payment.is_export_compta_id=False
                sql="""
                    SELECT  
                        aml.partner_id,
                        am.name,
                        am.date,
                        aa.code,
                        aa.name,
                        aml.name,
                        aml.debit,
                        aml.credit,
                        rp.name,
                        rp.ref,
                        aml.payment_id
                    FROM account_move_line aml inner join account_move am                on aml.move_id=am.id
                                            inner join account_account aa             on aml.account_id=aa.id
                                            left outer join res_partner rp            on aml.partner_id=rp.id
                                            inner join account_journal aj             on aml.journal_id=aj.id
                                            inner join account_payment ap             on aml.payment_id=ap.id
                    WHERE 
                        aml.date<='"""+str(obj.date_fin)+"""' and 
                        am.company_id="""+str(self.env.user.company_id.id)+""" and
                        aa.code='665100' and
                        ap.is_export_compta_id is null
                    ORDER BY aml.date
                """
                cr.execute(sql)
                for row in cr.fetchall():
                    payment_id = row[10]
                    payments = self.env['account.payment'].search([('id','=',payment_id)])
                    partner=False
                    for payment in payments:
                        payment.is_export_compta_id = obj.id
                        partner = payment.partner_id
                    if partner:
                        journal_code  = 'ESC'
                        ecriture_num  = row[1]
                        ecriture_date = row[2]
                        compte_num = row[3]
                        ct=ct+1
                        vals={
                            'export_compta_id': obj.id,
                            'ligne'           : ct,
                            'journal_code'           : journal_code,
                            'ecriture_num'           : ecriture_num,
                            'ecriture_date'          : ecriture_date,
                            'compte_num'             : compte_num,
                            'piece_ref'              : ecriture_num,
                            'piece_date'             : ecriture_date,
                            'ecriture_lib'           : row[5],
                            'debit'                  : row[6],
                            'credit'                 : row[7],
                            'payment_id'             : payment_id,
                        }
                        self.env['is.export.compta.ligne'].create(vals)
                        ct=ct+1
                        compte_num = partner.property_account_receivable_id.code
                        vals={
                            'export_compta_id': obj.id,
                            'ligne'           : ct,
                            'journal_code'           : journal_code,
                            'ecriture_num'           : ecriture_num,
                            'ecriture_date'          : ecriture_date,
                            'compte_num'             : compte_num,
                            'piece_ref'              : ecriture_num,
                            'piece_date'             : ecriture_date,
                            'ecriture_lib'           : row[5],
                            'debit'                  : row[7],
                            'credit'                 : row[6],
                            'payment_id'             : payment_id,
                        }
                        self.env['is.export.compta.ligne'].create(vals)



    def generer_fichier_action(self):
        cr=self._cr
        for obj in self:
            name='export-compta.csv'
            model='is.export.compta'
            attachments = self.env['ir.attachment'].search([('res_model','=',model),('res_id','=',obj.id),('name','=',name)])
            attachments.unlink()
            dest     = '/tmp/'+name
            f = codecs.open(dest,'wb',encoding='utf-8')
            f.write("ligne\tjournal_code\tecriture_num\tecriture_date\tcompte_num\tcomp_aux_num\tpiece_ref\tpiece_date\tecriture_lib\tdebit\tcredit\r\n")
            for row in obj.ligne_ids:
                f.write(str(row.ligne)+'\t')
                f.write(row.journal_code+'\t')
                f.write(row.ecriture_num+'\t')
                f.write(row.ecriture_date.strftime('%Y%m%d')+'\t')
                f.write(row.compte_num+'\t')
                f.write((row.comp_aux_num or '')+'\t')
                f.write(row.piece_ref+'\t')
                f.write(row.piece_date.strftime('%Y%m%d')+'\t')
                f.write(row.ecriture_lib+'\t')
                f.write(str(row.debit).replace('.','.')+'\t')
                f.write(str(row.credit).replace('.','.')+'\t')
                f.write('\r\n')
            f.close()
            r = open(dest,'rb').read()
            r=base64.b64encode(r)
            vals = {
                'name':        name,
                'datas_fname': name,
                'type':        'binary',
                'res_model':   model,
                'res_id':      obj.id,
                'datas':       r,
            }
            attachment = self.env['ir.attachment'].create(vals)
            obj.file_ids=[(6,0,[attachment.id])]


