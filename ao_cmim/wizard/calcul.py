from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields,exceptions, api, _
from openerp.exceptions import UserError

class calcul_cotisation (models.TransientModel):
    _name = 'cmim.calcul.cotisation'
    
        
    @api.onchange('fiscal_date')
    def onchange_fiscal_date(self):
        if(self.fiscal_date):
            date = str(datetime.strptime(self.fiscal_date, '%Y-%m-%d').year) + "-1-1"
            mydate = datetime.strptime(date, '%Y-%m-%d')
            self.fiscal_date = mydate
            
    @api.model
    def _get_domain(self):
        periodes = self.env['date.range'].search([])
        ids = []
        for periode in periodes :
            duree = (datetime.strptime(periode.date_end, '%Y-%m-%d') - datetime.strptime(periode.date_start, '%Y-%m-%d')).days
            if duree > 88 and duree < 92:
                ids.append(periode.id)
        return [('id', 'in', ids)]
    
    @api.onchange('fiscal_date')
    def onchange_field_id(self):
         if self.fiscal_date:
            periodes = self.env['date.range'].search([])
            ids = []
            dec_year = datetime.strptime(self.fiscal_date, '%Y-%m-%d').year
            for periode in periodes :
                duree = (datetime.strptime(periode.date_end, '%Y-%m-%d') - datetime.strptime(periode.date_start, '%Y-%m-%d')).days
                if duree > 88 and duree < 92 and dec_year == datetime.strptime(periode.date_end, '%Y-%m-%d').year and dec_year == datetime.strptime(periode.date_start, '%Y-%m-%d').year:
                    ids.append(periode.id)
            return {'domain':{'date_range_id': [('id', 'in', ids)]}}
    fiscal_date = fields.Date(string="Annee fiscale")
    date_range_id = fields.Many2one('date.range', 'Periode', domain=lambda self: self._get_domain())
    collectivite_ids = fields.Many2many('res.partner','calcul_cotisation_collectivite', 'calcul_id', 'partner_id', "Collectivites", domain = "[('customer','=',True),('is_company','=',True)]")
    
    
    @api.multi
    def create_cotisation_product_lines(self, cotisation_obj):
        cotisation_assure_lines = self.env['cmim.cotisation.assure.line'].search([('cotisation_id.id','=', cotisation_obj.id)])
        cotisation_product_obj = self.env['cmim.cotisation.product']
        for line in cotisation_assure_lines:
            cotisation_product_obj = cotisation_product_obj.search([('cotisation_id.id', '=', cotisation_obj.id), 
                                                                    ('product_id.id', '=', line.product_id.id),
                                                                    ('code', '=', line.code),
                                                                    ('type_product_id.id', '=', line.type_product_id.id)])
            
            if(cotisation_product_obj):
                cotisation_product_obj.write({'montant': cotisation_product_obj.montant + line.montant})
            else:
                cotisation_product_obj = cotisation_product_obj.create({'cotisation_id': cotisation_obj.id,
                                                                        'product_id': line.product_id.id,
                                                                        'code': line.code,
                                                                        'type_product_id': line.type_product_id.id,
                                                                        'montant' : line.montant
                                                                        })
                cotisation_obj.write({'cotisation_product_ids': [(4,cotisation_product_obj.id)]})
        return True
    
    
    @api.multi
    def can_calculate(self):
        collectivities = []
        for col in self.collectivite_ids:
            collectivities.append(col.id)
        if(self.env['cmim.cotisation'].search([('collectivite_id.id','in',collectivities), 
                                               ('state','=','valide'),
                                               ('date_range_id.id','=',self.date_range_id.id)])):
            return False
        elif (self.env['cmim.cotisation'].search([('collectivite_id.id','in',collectivities), 
                                               ('state','=','draft'),
                                               ('date_range_id.id','=',self.date_range_id.id)])) :
            for col in collectivities:        
                self._cr.execute(" DELETE FROM cmim_cotisation c where c.collectivite_id = %s and c.state = 'draft' and c.date_range_id = %s", (col,self.date_range_id.id))
            return True
        else:
            return True
        
    
    @api.multi
    def calcul_per_assure(self, declaration_id, contrat_ids, cotisation_assure_obj):

        cte_cnss = self.env['cmim.constante'].search([('name', '=', 'CNSS')])
        cte_sfp = self.env['cmim.constante'].search([('name', '=', 'SRP')])
        sal_men = (declaration_id.salaire/declaration_id.nb_jour)*30
        for contrat in contrat_ids:
            cotisation_line_dict = {'product_id': contrat.product_id.id,
                                    'code' : contrat.code,
                                    'cotisation_assure_id' : cotisation_assure_obj.id}
            
            if contrat.type_product_name == 'MAL':
                cotisation_line_dict['type_product_id'] = self.env['cmim.product.type'].search([('short_name', '=','MAL')]).id
                if(contrat.tarif_id.type == 'p'):
                    cotisation_line_dict['rate1'] = contrat.tarif_id.montant
                    if(sal_men < declaration_id.collectivite_id.secteur_id.plancher):
                        b_plancher = declaration_id.collectivite_id.secteur_id.plancher
                    else: 
                        b_plancher = sal_men
                    if( b_plancher < declaration_id.collectivite_id.secteur_id.plafond):
                        b_plafonnee = b_plancher
                    else:
                        b_plafonnee = declaration_id.collectivite_id.secteur_id.plafond
                    cotisation_line_dict['base1'] = b_plafonnee
                    cotisation_line_dict['montant'] = (b_plafonnee * contrat.tarif_id.montant)/ 100
                else: 
                    cotisation_line_dict['montant']  = contrat.tarif_id.montant
            else:
                cotisation_line_dict['type_product_id'] = self.env['cmim.product.type'].search([('short_name', '=','PRV')]).id
                if(cte_cnss.valeur > sal_men):
                    trancheA = sal_men
                else: 
                    trancheA = cte_cnss.valeur                
                if(sal_men > trancheA):
                    res = trancheA
                else : 
                    res = 0.0
                if(res > cte_sfp.valeur):
                    trancheB = cte_sfp.valeur
                else: 
                    trancheB = res
                cotisation_line_dict['base1'] = trancheA
                cotisation_line_dict['base2'] = trancheB  
                cotisation_line_dict['rate1'] = contrat.tarif_inc_deces_id.montant
                cotisation_line_dict['rate2'] = contrat.tarif_inv_id.montant
                cotisation_line_dict['montant'] = (trancheA * contrat.tarif_inc_deces_id.montant + trancheB * contrat.tarif_inv_id.montant) / 100
            cotisation_assure_obj.write({'cotisation_assure_line_ids':   [(0, 0, cotisation_line_dict)],
                                         'montant': cotisation_assure_obj.montant + cotisation_line_dict['montant']})
        return True
    
    
    @api.multi 
    def calcul_engine(self):
        if(not self.can_calculate()):
            raise exceptions.Warning(
                _("vous avez valide des cotisations pour une ou plusieurs collectivites. \nImpossible de lancer le calcul pour les memes periodes"))
        else: 
            cotisation_ids = []
            for col in self.collectivite_ids:
                cotisation_obj = self.env['cmim.cotisation'].create({  'date_range_id': self.date_range_id.id,
                                                                       'fiscal_date': self.fiscal_date,
                                                                       'collectivite_id': col.id
                                                                       })
                declaration_ids = self.env['cmim.declaration'].search([('collectivite_id.id','=',col.id),('fiscal_date','=',self.fiscal_date),('date_range_id.id','=',self.date_range_id.id)])
                for declaration_id in declaration_ids:
                    
                    cotisation_assure_obj = self.env['cmim.cotisation.assure'].create({    'cotisation_id': cotisation_obj.id,
                                                                                           'assure_id': declaration_id.assure_id.id})
                    cotisation_obj.write({'cotisation_assure_ids':   [(4, cotisation_assure_obj.id)]})
                    contrat_ids = self.env['cmim.contrat'].search([('collectivite_id.id','=',declaration_id.collectivite_id.id)])
                    self.calcul_per_assure(declaration_id, contrat_ids, cotisation_assure_obj)
                    cotisation_obj.write({'montant': cotisation_obj.montant + cotisation_assure_obj.montant})
                self.create_cotisation_product_lines(cotisation_obj)
                cotisation_ids.append(cotisation_obj.id)
            view_id = self.env.ref('ao_cmim.cotisation_tree_view').id

            return{ 
                    'res_model':'cmim.cotisation',
                    'type': 'ir.actions.act_window',
                    'res_id': self.id,
                    'view_mode':'tree,form',
                    'views' : [(view_id, 'tree'),(False, 'form')],
                    'view_id': 'ao_cmim.cotisation_tree_view',
                    'domain':[('id', 'in', cotisation_ids)],
                    'target':'self',
                    }
    
        
   




