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

from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import tabs

import logging

from openstack_dashboard.api import ceilometer

from openstack_dashboard.dashboards.admin.alarms import tables


LOG = logging.getLogger(__name__)


class ActiveAlarmsTab(tabs.TableTab):
    table_classes = (tables.ActiveAlarmsTable,)
    name = _("Active Alarms")
    slug = "active_alarms"
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_active_alarms_data(self):
        """ Active alarms """
        try:
            request = self.tab_group.request
            ceilometer_usage = ceilometer.CeilometerUsage(request)
            # ceilometer_usage.preload_all_users()
            # ceilometer_usage.preload_all_tenants()
            query = [{"field": "name", "op": "eq", "value": "ok"}]
            alarms = ceilometer.alarm_list(request, query=query,
                ceilometer_usage=ceilometer_usage)
        except Exception:
            alarms = []
            msg = _('Unable to retrieve list of active alarms.')
            exceptions.handle(self.request, msg)
        return alarms


class AllAlarmsTab(tabs.TableTab):
    table_classes = (tables.AllAlarmsTable,)
    name = _("All Alarms")
    slug = "all_alarms"
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_all_alarms_data(self):
        """ All alarms """
        try:
            request = self.tab_group.request
            ceilometer_usage = ceilometer.CeilometerUsage(request)
            # ceilometer_usage.preload_all_users()
            # ceilometer_usage.preload_all_tenants()
            alarms = ceilometer.alarm_list(request,
                                           ceilometer_usage=ceilometer_usage)
        except Exception:
            alarms = []
            msg = _('Unable to retrieve list of all alarms.')
            exceptions.handle(self.request, msg)
        return alarms


class AlarmManagementTabs(tabs.TabGroup):
    slug = "alarm_management"
    tabs = (AllAlarmsTab,ActiveAlarmsTab)
    sticky = True
