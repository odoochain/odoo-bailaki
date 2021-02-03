# Copyright 2021 - TODAY, Marcel Savegnago
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Bailaki',
    'description': """
        Bailaki Backend""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Marcel Savegnago',
    'website': 'https://popsolutions.co',
    'depends': [
        'partner_multi_relation_tabs',
        'partner_contact_birthplace',
        'partner_contact_birthdate',
        'partner_contact_nationality',
        'partner_contact_gender',
        'event',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/res_partner.xml',
        'security/res_partner_music_skill.xml',
        'security/res_partner_music_genre.xml',
        'views/res_partner_music_skill.xml',
        'views/res_partner_music_genre.xml',
        'views/res_partner.xml',
        'data/res_partner_relation.xml',
    ],
    'demo': [
    ],
}
