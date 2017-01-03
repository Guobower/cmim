# -*- coding: utf-8 -*-
{
    'name':'Comptabilité auxilière de la CMIM ',
    'author':'Agilorg',
    'website':'http://www.agilorg.com',
    'category': 'account',
    'description': """Comptabilité auxiliaire cmim""",
    'depends':['base','account','product', 'date_range'],
    'data':[
            'data/data_range_tye.xml',
            
            #'wizard/import_data.xml',
            'wizard/import_declarations_reglements.xml',
            'wizard/import_collectivites_assures.xml',
            'wizard/rapport.xml',
            'wizard/calcul.xml',
            'wizard/validation.xml',
            
            'views/date_range.xml',
            'views/product.xml',
            'views/cotisation.xml',
            'views/collectivite_assure.xml',
            'views/config.xml',
            'views/contrat.xml',
            'views/declaration.xml',
            'views/facture_paiement.xml',
            'views/menu.xml',

    ],
    'installable':True,
    'auto_install':False,
    'application':True,
}
