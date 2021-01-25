# Copyright 2020 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class ResPartnerMusicSkill(models.Model):

    _name = 'res.partner.music.skill'
    _description = 'Res Partner Music Skill'  # TODO

    name = fields.Char()
