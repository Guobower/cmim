
import openerp
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields, tools, api

class TypeProduit(models.Model):
    _name="cmim.product.type"
    name = fields.Char('Nom du type', required=True )
    short_name = fields.Char("code")
    
class Secteur(models.Model):
    _name = 'cmim.secteur'
    
    name = fields.Char('nom du secteur', reduired=True)
    plancher = fields.Float('Plancher du secteur')
    plafond = fields.Float('Plafond du secteur')

class ConstanteCalcul(models.Model):
    _name = 'cmim.constante'
    name = fields.Char('Nom ', required=True)
    valeur = fields.Char('Valeur ', required=True)
    
class Tarif(models.Model):
    _name='cmim.tarif'
    name = fields.Char('Nom', required = True)
    type = fields.Selection(selection= [('p', 'Taux'),
                                        ('f', 'Forfait')],
                                        required=True,
                                        default = "p",
                                        string='Type de tarif')
    montant = fields.Float('Tarif')    
    import_flag = fields.Boolean('Par import', default=False )       