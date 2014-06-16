# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import messages
from horizon import tabs

from openstack_dashboard.dashboards.admin.sla import tables

from openstack_dashboard.api import self_healing
from openstack_dashboard.api import nova
from openstack_dashboard.api import keystone

class SLATab(tabs.TableTab):
    table_classes = (tables.HealingActionsTable,)
    name = _("SLA")
    slug = "sla"
    template_name = ("horizon/common/_detail_table.html")

    def get_healing_actions_data(self):
        try:
            projects, more = keystone.tenant_list(self.request)
            action_parameters = []
            action_parameters = self_healing.get_action_parameters()
            #acts = self_healing.get_action_parameters()
            #action_parameters = self._copy(acts)

            for action in action_parameters:
                if (action.project == ''):
                    action.project = 'All Projects'
                elif action.project != 'All Projects':
                    action.project = self._get_tenant_name(action.project, projects)

            return action_parameters

        except Exception:
            msg = _('Unable to get self_healing action params.')
            exceptions.check_message(["Connection", "refused"], msg)

    def _get_tenant_name(self, tenant_id, projects):
        for p in projects:
            if p.enabled and p.id==tenant_id:
                return p.name
        return ''

class SLAVMResourcesTab(tabs.TableTab):
    table_classes = (tables.VMResourcesTable,)
    name = _("VM Status")
    slug = "vmresources"
    template_name = ("horizon/common/_detail_table.html")

    def get_vm_resources_data(self):
        try:
            projects, more = keystone.tenant_list(self.request)
            prj_details = {}
            for x in projects:
                prj_details[x.id] = x.name
            servers, more = nova.server_list(self.request, all_tenants=True)
            
            for x in servers:
                x.tenant_name = prj_details.get(x.tenant_id)
            return servers
        except Exception as e:
            msg = _('Unable to get vm resources status.')
            exceptions.check_message(["Connection", "refused"], msg)
            return []

class SLAHostResourcesTab(tabs.TableTab):
    table_classes = (tables.HostResourcesTable,)
    name = _("Hosts Status")
    slug = "hostresources"
    template_name = ("horizon/common/_detail_table.html")

    def get_host_resources_data(self):
        servers = []
        try:
            servers = nova.hypervisor_list(self.request)
            nova_services = nova.service_list(self.tab_group.request)
            for x in servers:
                x.state = self._get_service_state('nova-compute', x.hypervisor_hostname, nova_services)
                
        except Exception:
            msg = _('Unable to get hosts resources status.')
            exceptions.check_message(["Connection", "refused"], msg)
        return servers
    
    def _get_service_state(self, service_name, host, nova_services):
          #host,  state, binary (nova-compute)
           #nova_services[4]._info['state']
        for service in nova_services:
                if service.binary == service_name and service.host == host:
                    return service.state + ' | ' + service.status
        return ''

class SLALogs(tabs.TableTab):
    table_classes = (tables.SLALogsTable,)
    name = _("SLA Actions Logs")
    slug = "slaactionlogs"
    template_name = ("horizon/common/_detail_table.html")

    def get_sla_logs_data(self):
        sla_logs = []
        try:
            sla_logs = self_healing.get_sla_logs()
            if sla_logs:
              log_count = self.request.session.get('sla_log_count', len(sla_logs))
              if int(log_count) > len(sla_logs):
                  messages.warning(self.request, "New Tracking LOG")
            self.request.session['sla_log_count'] = len(sla_logs)
        except Exception:
            msg = _('Unable to get sla action logs status.')
            exceptions.check_message(["Connection", "refused"], msg)

        return sla_logs


class SLATabs(tabs.TabGroup):
    slug = "slas"
    tabs = (SLATab,SLAHostResourcesTab, SLAVMResourcesTab, SLALogs,)
    sticky = True
