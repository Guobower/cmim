
import openerp
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields, tools, api

class collectivite(models.Model):
    _inherit = "res.partner"
    _sql_constraints = [
        ('code_collectivite_uniq', 'unique(code)', 'le code d\'adherent doit etre unique'),
    ]
    _defaults = {
        'company_type': 'company',
        'is_company': True,
        'customer' : True
        }
    @api.one
    @api.depends('assure_ids')
    def _assures_count(self):
        
        for obj in self:
            if self.assure_ids :
                obj.assures_count = len(self.assure_ids)
            
    import_flag = fields.Boolean('Par import', default=False)      
    code = fields.Char(string="Code collectivite", required=True, copy=False)
    name = fields.Char(string="Raison sociale", required=True)
    date_adhesion = fields.Date(string="date d\'adhesion", required=True)
    secteur_id = fields.Many2one('cmim.secteur', "Secteur", required=True)
    contrat_ids = fields.One2many('cmim.contrat', 'collectivite_id', string="Contrats")
    assure_ids = fields.One2many('cmim.assure', 'collectivite_id', string="Assures associes")
    assures_count = fields.Integer(compute='_assures_count', string="Nb assures")

    @api.multi
    def get_assures(self):
        view_id = self.env.ref('ao_cmim.view_assure_tree').id
        return{ 
                'res_model':'cmim.assure',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'view_mode':'tree,form',
                'views' : [(view_id, 'tree'),(False, 'form')],
                'view_id': 'ao_cmim.view_assure_tree',
                'target':'self',
                'domain':[('collectivite_id.id', '=', self.id)],
                }
    
    @api.multi
    def get_payments(self):
        view_id = self.env.ref('account.view_account_payment_tree').id
        return{ 
                'res_model':'account.payment',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'view_mode':'tree,form',
                'views' : [(view_id, 'tree'),(False, 'form')],
                'view_id': 'account.view_account_payment_tree',
                'target':'self',
                'domain':[('partner_id.id', '=', self.id)],
                }
    
    @api.multi
    def get_declarations(self):
        view_id = self.env.ref('ao_cmim.declaration_tree_view').id
        return{ 
                'res_model':'cmim.declaration',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'view_mode':'tree',
                'views' : [(view_id, 'tree'),(False, 'form')],
                'view_id': 'ao_cmim.declaration_tree_view',
                'target':'self',
                'domain':[('collectivite_id.id', '=', self.id)],
                'context':{'group_by':'payroll_period_id'},
                }
    @api.multi
    def get_cotisations(self):
        view_id = self.env.ref('ao_cmim.cotisation_tree_view').id
        return{ 
                'res_model':'cmim.cotisation',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'view_mode':'tree',
                'views' : [(view_id, 'tree'),(False, 'form')],
                'view_id': 'ao_cmim.cotisation_tree_view',
                'target':'self',
                'domain':[('state', '=', 'draft'),('collectivite_id.id', '=', self.id)],
                'context':{'group_by':'payroll_period_id'},
                }
    
    @api.multi
    def import_declaration(self):
        return True

class assure(models.Model):
    _name = 'cmim.assure'

    """_sql_constraints = [
        ('numero_uniq', 'unique(numero)', 'le code d\'assure doit etre unique'),
    ]"""
    _defaults = {
        'statut': 'active',
        'is_normal' : True,
        }
    
    def _get_default_image(self):
        img_path = openerp.modules.get_module_resource(
            'base', 'static/src/img', 'avatar.png')
        with open(img_path, 'rb') as f:
            image = f.read()
        return tools.image_resize_image_big(image.encode('base64'))
    
    import_flag = fields.Boolean('Par import', default=False)      
    name = fields.Char('Nom', required=True)
    image = openerp.fields.Binary("Image", attachment=True,
        help="This field holds the image used as avatar for this contact, limited to 1024x1024px",
        default=lambda self: self._get_default_image())
    email = fields.Char('Email')
    phone = fields.Char('Phone')
    mobile = fields.Char('Mobile')
    street = fields.Char('Street')
    city = fields.Char('City')
    state_id = fields.Many2one("res.country.state", 'State', ondelete='restrict')
    zip = fields.Char('Zip', size=24, change_default=True)
    country_id = fields.Many2one('res.country', 'Country', ondelete='restrict')
    
    
    id_num_famille = fields.Integer(string="Id Numero Famille")
    numero = fields.Integer(string="Numero Assure", required=True)
    collectivite_id = fields.Many2one('res.partner', string='Collectivite', domain="[('customer','=',True),('is_company','=',True)]", required=True, ondelete='cascade')
    statut = fields.Selection(selection=[('active', 'Actif'),
                                          ('invalide', 'Invalide'),
                                          ('retraite', 'Retraite')],
                                           required=True,
                                           string='Statut')
    
    date_naissance = fields.Date(string="Date de naissance")
    is_normal = fields.Boolean('Est Normal')
    
    parent_id =  fields.Many2one('cmim.assure', 'Assure contractant')
    epoux_id =  fields.Many2one('cmim.assure', 'Epoux (se)')
    declaration_ids = fields.Many2one('cmim.declaration', 'Declarations')    
    
    @api.onchange('epoux_id', 'collectivite_id')
    def onchange_assure(self):
        if(self.epoux_id):
            self.id_num_famille =  self.epoux_id.id_num_famille       
        else:
            self.id_num_famille=None     
        if (self.collectivite_id):
            return {'domain': {'epoux_id': [('collectivite_id.id', '=', self.collectivite_id.id)]}}
    @api.model
    def create(self, vals):
        tools.image_resize_images(vals)
        partner = super(assure, self).create(vals)
        return partner

    @api.multi
    def get_ayant_droits(self):
        view_id = self.env.ref('ao_cmim.view_assure_tree').id
        return{ 
                'res_model':'cmim.assure',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'view_mode':'tree,form',
                'views' : [(view_id, 'tree'),(False, 'form')],
                'view_id': 'ao_cmim.view_assure_tree',
                'target':'self',
                'domain':[('parent_id.id', '=', self.id)],
                }

    @api.multi
    def get_declarations(self):
        view_id = self.env.ref('ao_cmim.declaration_tree_view').id
        return{ 
                'res_model':'cmim.declaration',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'view_mode':'tree',
                'views' : [(view_id, 'tree'),(False, 'form')],
                'view_id': 'ao_cmim.declaration_tree_view',
                'target':'self',
                'domain':[('assure_id.id', '=', self.id)],
                }
        return True
    
    @api.multi
    def get_cotisations(self):
        """view_id = self.env.ref('ao_cmim.view_assure_tree').id
        return{ 
                'res_model':'cmim.assure',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'view_mode':'tree,form',
                'views' : [(view_id, 'tree'),(False, 'form')],
                'view_id': 'ao_cmim.view_assure_tree',
                'target':'self',
                'domain':[('parent_id.id', '=', self.id)],
                }"""
        return True
    
    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False, lazy=True):
        if 'numero' in fields:
            fields.remove('numero')
        if 'id_num_famille' in fields:
            fields.remove('id_num_famille')
        return super(assure, self).read_group(cr, uid, domain, fields, groupby, offset, limit=limit, context=context, orderby=orderby, lazy=True)
    
        
        
        
        
        