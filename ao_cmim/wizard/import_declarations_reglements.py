# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import date
from openerp import fields, models, exceptions, api, _
import base64
import csv
import cStringIO
from openerp.exceptions import UserError
#############################################################################

class cmimImportDecPay(models.TransientModel):
    
    _name = 'cmim.import.dec.pay'

    data = fields.Binary("Fichier", required=True)
    delimeter = fields.Char('Delimeter', default=';',
                            help='Default delimeter is ";"')
    type_operation = fields.Selection(selection=[('declaration', u'Déclarations'),
                                         ('reglement', 'Encaissements')],
                                           required=True,
                                           string=u"Type d'opération",
                                           default='declaration')
    systeme = fields.Selection(selection=[('old', 'Ancien'), ('new', 'Nouveau')],string=u"Type Matricule Assué", defalut='new', required=True)
    model = fields.Selection(selection=[('1', 'Trimestrielle'), ('2', 'Par mois')], string=u"Périodicité", defalut='1', required=True)
    payment_date = fields.Date(string=u"Date de réglement")
    
    def _default_journal(self):
        domain = [
            ('type', '=', 'bank'),
            ('company_id', '=', self.env.user.company_id.id),
        ]
        return self.env['account.journal'].search(domain, limit=1)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get())
    journal_id = fields.Many2one('account.journal', string='Journal',
        default=_default_journal, domain="[('company_id', '=', company_id),('type', '=', 'bank')]", required=True)
    @api.onchange('fiscal_date')
    def onchange_fiscal_date(self):
        if(self.fiscal_date):
            periodes = self.env['date.range'].search([])
            ids = []
            for periode in periodes :
                duree = (datetime.strptime(periode.date_end, '%Y-%m-%d') - datetime.strptime(periode.date_start, '%Y-%m-%d')).days
                if duree > 88 and duree < 92 and self.fiscal_date == datetime.strptime(periode.date_end, '%Y-%m-%d').year and self.fiscal_date == datetime.strptime(periode.date_start, '%Y-%m-%d').year:
                    ids.append(periode.id)
            return {'domain':{'date_range_id': [('id', 'in', ids)]}}
    
    fiscal_date = fields.Integer(string=u"Année Comptable", required=True, default= datetime.now().year )
    date_range_id = fields.Many2one('date.range', 'Periode', required=True)
    
    @api.multi
    def import_declarations(self, reader_info):
        declaration_obj = self.env['cmim.declaration']
        partner_obj = self.env['res.partner']
        list_to_import = []
        ids = []
        assure_obj = self.env['res.partner']
        if(self.model == "1"):
            for i in range(len(reader_info)):
                values = reader_info[i]
                salaire = float('.'.join(str(x) for x in tuple(values[6].split(','))))
                if(not salaire == 0):
                    partner_obj = partner_obj.search([('numero', '=', values[3]),('collectivite_id.code', '=', values[0])])
                    if partner_obj.search([('numero', '=', values[3]),('collectivite_id.code', '=', values[0])]):
                            list_to_import.append({ 
                                    'collectivite_id': collectivite_obj.search([('code', '=', values[0])]).id,
                                    'assure_id': partner_obj.id,
                                    'nb_jour' : values[7],
                                    'salaire': salaire,
                                    'import_flag': True,
                                    'fiscal_date': self.fiscal_date,
                                    'date_range_id': self.date_range_id.id
                                                     })
            print len(list_to_import)
            for line in list_to_import:
                declaration_obj= declaration_obj.search([('assure_id', '=', line['assure_id']), ('date_range_id', '=', line['date_range_id'])])
                if not declaration_obj:
                    declaration_obj = declaration_obj.create(line)
                    ids.append(declaration_obj.id)
        elif(self.model == "2"):
            collectivite_obj = collectivite_obj.search([('code', '=', reader_info[i][0])])
            del reader_info[0]
            for i in range(len(reader_info)):
                values = reader_info[i]
                salaire = float('.'.join(str(x) for x in tuple(values[1].split(',')))) + float('.'.join(str(x) for x in tuple(values[3].split(',')))) + float('.'.join(str(x) for x in tuple(values[5].split(','))))
                if(not salaire == 0):
                    assure = self.env['cmim.assure'].search([('numero', '=', values[0]), ('collectivite_id.id', '=', collectivite_obj.id)])
                    if(assure):
                        if(not declaration_obj.search([('assure_id.id', '=', assure.id), ('fiscal_date', '=', self.fiscal_date), ('date_range_id.id', '=', self.date_range_id.id)])):
                            declaration_obj.create({ 'collectivite_id': collectivite_obj.id,
                                                     'assure_id': assure.id,
                                                     'nb_jour' : values[2] + values[4] + values[6],
                                                     'salaire': salaire,
                                                     'import_flag': True,
                                                     'fiscal_date': self.fiscal_date,
                                                    'date_range_id': self.date_range_id.id
                                                    })
        if len(ids)>0: 
                view_id = self.env.ref('ao_cmim.declaration_tree_view').id
                return{ 
                    'name': u'Déclarations importées',
                    'res_model':'cmim.declaration',
                    'type': 'ir.actions.act_window',
                    'res_id': self.id,
                    'view_mode':'tree,form',
                    'views' : [(view_id, 'tree'),(False, 'form')],
                    'view_id': 'ao_cmim.declaration_tree_view',
                    'target':'self',
                    'domain':[('id', 'in', ids)],
                    }    
        else:
            return True   
############################################################################

    @api.multi
    def import_reglements(self, reader_info):
        collectivite_obj = self.env['res.partner']
        codes = [int(reader_info[i][0]) for i in range(len(reader_info))]
        list_to_import = []
        ids = []
        account_obj = self.env['account.payment']
        for i in range(len(reader_info)):
            val = {}
            values = reader_info[i]
            collectivite_obj = collectivite_obj.search([('code', '=', values[0])])
            if(collectivite_obj):
                vals = {        'partner_id' : collectivite_obj.id,
                                'journal_id': self.journal_id.id,
                                'payment_method_id' : 1,
                                'payment_type' : 'inbound',
                                'partner_type' : 'customer',
                                'import_flag': True,
                                'payment_date': self.payment_date,
                                'amount' : float('.'.join(str(x) for x in tuple(values[2].split(',')))),
                                
                                }
                list_to_import.append(vals)
        for line in list_to_import:
            account_obj =  account_obj.search([('partner_id', '=', line['partner_id']), ('journal_id', '=', line['journal_id']), ('payment_date', '=', line['payment_date'])])
            if not account_obj:
                account_obj = account_obj.create(line)
                ids.append(account_obj.id)
            else:
                account_obj.write(line)
            
        if len(ids)>0: 
            view_id = self.env.ref('account.view_account_payment_tree').id
            return{ 
                'name': 'Encaissements importes',
                'res_model':'account.payment',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'view_mode':'tree,form',
                'views' : [(view_id, 'tree'),(False, 'form')],
                'view_id': 'account.view_account_payment_tree',
                'target':'self',
                'domain':[('id', 'in', ids)],
                }
#                 account_obj = self.env['account.payment'].create(vals)
#                 account_obj.post()

############################################################################

    @api.multi
    def import_dec_pay(self):
        data = base64.b64decode(self.data)
        file_input = cStringIO.StringIO(data)
        file_input.seek(0)
        reader_info = []
        if self.delimeter:
            delimeter = str(self.delimeter)
        else:
            delimeter = ';'
        reader = csv.reader(file_input, delimiter=delimeter,
                            lineterminator='\r\n')
        try:
            reader_info.extend(reader)
        except Exception:
            raise exceptions.Warning(_(u"Le fichier sélectionné n'est pas valide!"))
        
        if(not self.env['res.partner'].search([('is_collectivite', '=', True)])):
                raise exceptions.Warning(_(u"L'import des encaissements exige l'existances des collectivités dans le système, veuillez créer les collectivités en premier"))
        else:
            if self.type_operation == 'declaration':
                    return self.import_declarations(reader_info)
            elif self.type_operation == 'reglement':
                    return self.import_reglements(reader_info)
            
