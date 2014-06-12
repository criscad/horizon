# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging

from django.core.urlresolvers import reverse  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import tables
from openstack_dashboard import api


LOG = logging.getLogger(__name__)


class DeleteAlarm(tables.DeleteAction):
    data_type_singular = _("Alarm")
    data_type_plural = _("Alarms")

    def delete(self, request, obj_id):
        try:
            api.ceilometer.alarm_delete(request, obj_id)
        except Exception:
            msg = _('Failed to delete alarm %s') % obj_id
            LOG.info(msg)
            redirect = reverse('horizon:admin:alarms:index')
            exceptions.handle(request, msg, redirect=redirect)


class CreateAlarm(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Alarm")
    url = "horizon:admin:alarms:create"
    classes = ("ajax-modal", "btn-create")


class EditAlarm(tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Alarm")
    url = "horizon:admin:alarms:update"
    classes = ("ajax-modal", "btn-edit")

# TODO(lsmola) rather than multiple tabs, it would be cool to have
# a selectboxes, where when can filter which type of alarms we wan to show


class ActiveAlarmsTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         sortable=True)
    tenant = tables.Column("tenant",
                           verbose_name=_("Project"),
                           sortable=True,
                           filters=(lambda x: getattr(x, 'name', ""),))
    user = tables.Column("user",
                         verbose_name=_("User id"),
                         sortable=True,
                         filters=(lambda x: getattr(x, 'name', ""),))
    description = tables.Column("description",
                                verbose_name=_("Description"),
                                sortable=True)
    state = tables.Column("state",
                         verbose_name=_("State"),
                         sortable=True)
    state_timestamp = tables.Column("state_timestamp",
                                    verbose_name=_("State Timestamp"),
                                    sortable=True)

    class Meta:
        name = "active_alarms"
        verbose_name = _("Currently active alarms")
        table_actions = (CreateAlarm, DeleteAlarm)
        row_actions = (EditAlarm, DeleteAlarm)


class AllAlarmsTable(ActiveAlarmsTable):

    class Meta:
        name = "all_alarms"
        verbose_name = _("All alarms")
        table_actions = (CreateAlarm, DeleteAlarm)
        row_actions = (EditAlarm, DeleteAlarm)
