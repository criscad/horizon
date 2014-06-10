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

from django import template
from django.template import defaultfilters as filters
from django.utils.translation import ugettext_lazy as _

from horizon import tables
from horizon.utils import filters as utils_filters

from openstack_dashboard import api



#class NovaServiceFilterAction(tables.FilterAction):
#    def fi
#       def comp(service):
#          lter(self, table, services, filter_string):
#        q = filter_string.lower()
#  if q in service.type.lower():
#               return True
#            return False
#
#        return filter(comp, services)

class CreateHealingAction(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Healing Action")
    url = "horizon:admin:sla:create"
    classes = ("ajax-modal", "btn-create")
    #policy_rules = (('identity', 'identity:create_grant'),
    #                ("identity", "identity:create_user"),
    #                ("identity", "identity:list_roles"),
    #                ("identity", "identity:list_projects"),)
    #
    #def allowed(self, request, user):
    #    return api.keystone.keystone_can_edit_user()


class DeleteHealingActionsAction(tables.DeleteAction):
    data_type_singular = _("Healing Action")
    data_type_plural = _("Healing Actions")
    #policy_rules = (("identity", "identity:delete_user"),)

    #def allowed(self, request, datum):
    #    if not api.keystone.keystone_can_edit_user() por \
    #            (datum and datum.id == request.user.id):
    #        return False
    #    return True

    def delete(self, request, obj_id):
        api.self_healing.delete_action_parameters(obj_id)

class SLALogsDetailsAction(tables.LinkAction):
    name = "actiondetails"
    verbose_name = _("SLA Action Details")
    #url = "horizon:admin:sla:action_details"
    url = "horizon:admin:sla:actiondetails"
    classes = ("ajax-modal", "btn-create")
    #policy_rules = (('identity', 'identity:create_grant'),
    #                ("identity", "identity:create_user"),
    #                ("identity", "identity:list_roles"),
    #                ("identity", "identity:list_projects"),)
    #
    #def allowed(self, request, user):
    #    return api.keystone.keystone_can_edit_user()


class HealingActionsTable(tables.DataTable):
    id = tables.Column("id", verbose_name=_('ID'))
    project = tables.Column("project", verbose_name=_('Project'))
    condition = tables.Column('condition', verbose_name=_('Condition'))
    action = tables.Column('action', verbose_name=_('Action'))
    #period = tables.Column('period', verbose_name=_('Period'))


    def get_object_id(self, obj):
        return "%s" % (obj.id)

    class Meta:
        name = "healing_actions"
        verbose_name = _("Healing Actions")
        table_actions = (CreateHealingAction, DeleteHealingActionsAction)
        row_actions = (DeleteHealingActionsAction,)
        multi_select = True

class VMResourcesTable(tables.DataTable):
    ip = tables.Column("ip", verbose_name=_('VM IP'))
    vm = tables.Column('vm', verbose_name=_('VM Name'))
    project = tables.Column("project", verbose_name=_('Project'))
    host = tables.Column('host', verbose_name=_('Host Name'))
    status = tables.Column('status', verbose_name=_('VM Status'))

    def get_object_id(self, obj):
        return "%s" % (obj.ip)

    class Meta:
        name = "vm_resources"
        verbose_name = _("VM Resources Status")
        table_actions = ()


class HostResourcesTable(tables.DataTable):
    ip = tables.Column("ip", verbose_name=_('Host IP'))
    host = tables.Column('host', verbose_name=_('Host Name'))
    loaded = tables.Column('loaded', verbose_name=_('Loaded'))
    running_vms = tables.Column('running_vms', verbose_name=_('# Running VMs'))
    compute_service_status = tables.Column('compute_service_status', verbose_name=_('Compute Service Status'))

    def get_object_id(self, obj):
        return "%s" % (obj.ip)

    class Meta:
        name = "host_resources"
        verbose_name = _("Host Resources Status")
        table_actions = ()

class SLALogsTable(tables.DataTable):
    id = tables.Column("id", verbose_name=_('Tracking ID'))
    date = tables.Column('date', verbose_name=_('Date'))
    alarm = tables.Column('alarm', verbose_name=_('Triggered Alarm'))
    resources = tables.Column('resources', verbose_name=_('Associated Resources'))

    def get_object_id(self, obj):
        return "%s" % (obj.id)

    class Meta:
        name = "sla_logs"
        verbose_name = _("SLA Tracking Logs")
        table_actions = ()
        row_actions = (SLALogsDetailsAction,)

class SLALogsDetailsTable(tables.DataTable):
    id = tables.Column("id", verbose_name=_('Action ID'))
    date = tables.Column('date', verbose_name=_('Date'))
    action = tables.Column('action', verbose_name=_('Triggered Action'))
    target_id = tables.Column('target_id', verbose_name=_('Target Resource'))
    output = tables.Column('output', verbose_name=_('Resource Name'))
    status = tables.Column('status', verbose_name=_('Status'))


    def get_object_id(self, obj):
        return "%s" % (obj.id)

    class Meta:
        name = "sla_logs_details"
        verbose_name = _("SLA Actions Logs Details")
        table_actions = ()
        row_actions = ()