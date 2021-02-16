# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from datetime import timedelta


class ResPartnerRelation(models.Model):

    _inherit = 'res.partner.relation'

    @api.model
    def _cron_unmatch_relation_clean(self):
        """
            Verify and remove unmatches
        """
        unmatch_id = self.env.ref("bailaki.relation_type_unmatch")

        for relation in self.search([('type_id', '=', unmatch_id.id)]):
            if (relation.create_date):
                if (relation.create_date + timedelta(days=30) < fields.datetime.now()):
                    relation.unlink()
