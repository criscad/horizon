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
            action_parameters = []
            action_parameters = self_healing.get_action_parameters()
            #acts = self_healing.get_action_parameters()
            #action_parameters = self._copy(acts)

            for action in action_parameters:
                if (action.project == ''):
                    action.project = 'All Projects'
                elif action.project != 'All Projects':
                    action.project = self._get_tenant_name(action.project)

            return action_parameters

        except Exception:
            msg = _('Unable to get self_healing action params.')
            exceptions.check_message(["Connection", "refused"], msg)

    #def _copy(self, list):
    #    l = []
    #    for x in list:
    #        y = SLATab.HealingAction()
    #        y.condition = x.condition
    #        y.action = x.action
    #        y.project = x.project
    #        y.period = x.period
    #        y.id = x.id
    #        l.append(y)
    #    return l

    def _get_tenant_name(self, tenant_id):
        projects = keystone.tenant_list(self.request)
        for p in projects[0]:
            if p.enabled and p.id==tenant_id:
                return p.name
        return ''

    #class HealingAction():
    #    condition = 'a'
    #    action = 'a'
    #    project = 'a'
    #    period ='a'
    #    id = 'a'

class SLAVMResourcesTab(tabs.TableTab):
    table_classes = (tables.VMResourcesTable,)
    name = _("VM Status")
    slug = "vmresources"
    template_name = ("horizon/common/_detail_table.html")

    def get_vm_resources_data(self):
        try:
            #self.vm_resources = self_healing.get_vm_resources_status()

            servers = nova.server_list(self.request,all_tenants=True)
            vm_resources = []
            if servers and servers[0]:
                r = range(0, servers[0].__len__(), 1)
                for i in r:
                    vm = SLAVMResourcesTab.VMResources(servers[0][i]._apiresource.networks['private'][0],
                                self._get_tenant_name(servers[0][i]._apiresource.tenant_id),
                                servers[0][i]._apiresource.human_id,
                                servers[0][i]._apiresource._info['OS-EXT-SRV-ATTR:hypervisor_hostname'],
                                servers[0][i]._apiresource.status)
                    #servers[0][i]._apiresource._loaded,
                    vm_resources.append(vm)
            return vm_resources

        except Exception:
            msg = _('Unable to get vm resources status.')
            exceptions.check_message(["Connection", "refused"], msg)


    def _get_tenant_name(self, tenant_id):
        projects = keystone.tenant_list(self.request)
        for p in projects[0]:
            if p.enabled and p.id==tenant_id:
                return p.name
        return ''

    class VMResources():
        status = ''
        project = ''
        host = ''
        vm =''
        ip = ''
        def __init__(self, ip, project, vm, host, status):
            self.status = status
            self.project = project
            self.host = host
            self.vm = vm
            self.ip = ip


class SLAHostResourcesTab(tabs.TableTab):
    table_classes = (tables.HostResourcesTable,)
    name = _("Hosts Status")
    slug = "hostresources"
    template_name = ("horizon/common/_detail_table.html")

    def get_host_resources_data(self):
        try:
            #self.host_resources = self_healing.get_host_resources_status()
            servers = nova.hypervisor_list(self.request)

            nova_services = nova.service_list(self.tab_group.request)

            host_resources = []

            if nova_services and servers:
                r = range(0, servers.__len__(), 1)
                for i in r:
                    service_state = self._get_service_state('nova-compute', servers[i].hypervisor_hostname, nova_services)
                    host = SLAHostResourcesTab.HostResources(servers[i].host_ip, servers[i].hypervisor_hostname, str(servers[i]._loaded), str(servers[i].running_vms), service_state)
                    host_resources.append(host)

            return host_resources

        except Exception:
            msg = _('Unable to get hosts resources status.')
            exceptions.check_message(["Connection", "refused"], msg)

    def _get_service_state(self, service_name, host, nova_services):
          #host,  state, binary (nova-compute)
           #nova_services[4]._info['state']
        for service in nova_services:
                if service._info['binary'] == service_name and service._info['host'] == host:
                    return service._info['state']
        return ''

    class HostResources():
        loaded = ''
        host =''
        ip = ''
        running_vms = ''
        compute_service_status = ''
        def __init__(self, ip, host, loaded, running_vms, compute_service_status):
            self.loaded = loaded
            self.host = host
            self.ip = ip
            self.running_vms = running_vms
            self.compute_service_status = compute_service_status

class SLALogs(tabs.TableTab):
    table_classes = (tables.SLALogsTable,)
    name = _("SLA Actions Logs")
    slug = "slaactionlogs"
    template_name = ("horizon/common/_detail_table.html")
    sla_logs = []

    def get_sla_logs_data(self):
        try:
            self.sla_logs = self_healing.get_sla_logs()
        except Exception:
            msg = _('Unable to get sla action logs status.')
            exceptions.check_message(["Connection", "refused"], msg)

        return self.sla_logs


class SLATabs(tabs.TabGroup):
    slug = "slas"
    tabs = (SLATab,SLAHostResourcesTab,SLAVMResourcesTab,SLALogs)
    sticky = True
