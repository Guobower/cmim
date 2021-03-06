# -*- coding: utf-8 -*-
{
    'name':'Comptabilité auxilière de la CMIM ',
    'author':'Agilorg',
    'website':'http://www.agilorg.com',
    'category': 'account',
    'description': """Comptabilité auxiliaire cmim""",
    'depends':['base',
               'account',
               'product', 
               'date_range'],
    'data':[
            'data/data_range_tye.xml',
            'data/product_template.xml',
            'data/secteurs.xml',
            'data/statut_assure.xml',
            'data/constante_calcul.xml',
            'data/garantie.xml',
            'data/cotisation_seq.xml',
            'data/contrat_seq.xml',
            'data/regle_calcul_data.xml',
            
            'wizard/import_declarations_reglements.xml',
            'wizard/import_collectivites_assures.xml',
            'wizard/rapport.xml',
            'wizard/calcul.xml',
            'wizard/validation.xml',
            'wizard/date_range_generator.xml',
            'wizard/import_assure_state.xml',

            'views/date_range.xml',
            'views/product.xml',
            'views/cotisation.xml',
            'views/collectivite.xml',
            'views/config.xml',
            'views/regle_calcul.xml',
            'views/contrat.xml',
            'views/declaration.xml',
            'views/facture_paiement.xml',
            'views/menu.xml',

    ],
    'sequence': 1,
    'installable': True,
    'application': True,
    'auto_install': False,
}
