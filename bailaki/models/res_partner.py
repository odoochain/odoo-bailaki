# Copyright 2020 - TODAY, Marcel Savegnago
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from math import radians, cos, sin, asin, sqrt

# Formula de Haversine
def haversine(a, b):
    # Raio da Terra em Km
    r = 6371

    # Converte coordenadas de graus para radianos
    lon1, lat1, lon2, lat2 = map(radians, [a['partner_current_longitude'], a['partner_current_latitude'], b['partner_current_longitude'], b['partner_current_latitude']])

    # Formula de Haversine
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    hav = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    d = 2 * r * asin(sqrt(hav))

    return d


class ResPartner(models.Model):

    _inherit = 'res.partner'


    profile_description = fields.Text(string="Profile Description", size=140)

    music_genre_ids = fields.Many2many(
        'res.partner.music.genre',
        string='Music Genres'
    )

    music_skill_id = fields.Many2one(
        'res.partner.music.skill',
        string='Music Skill'
    )

    referred_friend_ids = fields.Many2many('res.partner',
                                          string="Referred Friends",
                                          compute='_compute_referred_friend_ids')

    referred_friend_count = fields.Integer(
        compute="_compute_referred_friend_count",
        string='# Referred Friends')

    referred_friend_max_distance = fields.Integer(
        string="Referred Friend Max Distance",
        default=25,
    )

    referred_friend_gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ])

    partner_current_latitude = fields.Float(
        string='Geo Current Latitude',
        digits=(16, 5),
    )

    partner_current_longitude = fields.Float(
        string='Geo Current Longitude',
        digits=(16, 5),
    )

    @api.depends('referred_friend_ids')
    def _compute_referred_friend_count(self):
        for rec in self:
            rec.inspection_count = len(
                rec.referred_friend_ids)

    @api.depends('relation_all_ids')
    def _compute_match_relation(self):
        for rec in self:
            send_likes = rec.relation_all_ids.filtered(
                lambda x: x.this_partner_id == rec and
                          x.tab_id.code == 'send_likes'
            )
            for send in send_likes:
                if not rec.relation_all_ids.filtered(
                        lambda x: x.tab_id.code == 'matches' and
                                  x.other_partner_id == send.other_partner_id):

                    match = rec.relation_all_ids.filtered(
                        lambda x: x.this_partner_id == rec and
                                  x.tab_id.code == 'receive_likes' and
                                  x.other_partner_id == send.other_partner_id)

                    if match:
                        # Cria relação do tipo match
                        rec.env['res.partner.relation'].create({
                            'type_id': rec.env.ref('bailaki.relation_type_match').id,
                            'left_partner_id': rec.id,
                            'right_partner_id': match.other_partner_id.id})

                        # Envia notificação via OdooBot para os envolvidos no match
                        rec.env['mail.channel'].sudo().message_post(
                            body='<p>Match entre %s e %s</p>' % (
                            match.this_partner_id.name, match.other_partner_id.name),
                            subtype='mail.mt_comment',
                            model='mail.channel',
                            partner_ids=[match.this_partner_id.id, match.other_partner_id.id]
                        )

    @api.multi
    def _compute_referred_friend_ids(self):
        for rec in self:
            if rec.id and rec.is_company == False:
                friend_ids = rec.env['res.partner'].sudo().\
                    search([
                     '&', '&', '&', ('active', '=', True),
                    ('id', '!=', rec.id),
                    ('gender', '=', rec.referred_friend_gender),
                    ('is_company', '=', False),
                ])
                if friend_ids:
                    friend_ids = friend_ids.filtered(
                    (lambda x: haversine(x, rec) <= rec.referred_friend_max_distance)
                )
                rec.referred_friend_ids = friend_ids
                # Todo: esta checagem deve ocorrer quando houver alguma ateração nas relações entre parceiros
                rec._compute_match_relation()

    @api.multi
    def action_view_referred_friend(self):
        action = self.env.ref(
            "contacts.action_contacts").read()[0]
        action["domain"] = [("id", "in", self.referred_friend_ids.ids)]
        return action
