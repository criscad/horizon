# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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

from horizon import tabs
import operator

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.decorators import method_decorator  # noqa
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_post_parameters  # noqa

from horizon import exceptions
from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.sla import tabs as project_tabs

from horizon import forms
from horizon import tables

from openstack_dashboard.dashboards.admin.sla import tables as project_tables
from openstack_dashboard.api import self_healing

from openstack_dashboard.dashboards.admin.sla \
    import forms as project_forms

from django.views.generic import View as generic_view # noqa
from django.http import HttpResponse
import json

class IndexView(tabs.TabbedTableView):
    tab_group_class = project_tabs.SLATabs
    template_name = 'admin/sla/index.html'
    

class CreateView(forms.ModalFormView):
    form_class = project_forms.CreateHealingActionForm
    template_name = 'admin/sla/create.html'
    success_url = reverse_lazy('horizon:admin:sla:index')

    @method_decorator(sensitive_post_parameters('password',
                                                'confirm_password'))
    def dispatch(self, *args, **kwargs):
        return super(CreateView, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(CreateView, self).get_form_kwargs()
        try:
            roles = api.keystone.role_list(self.request)
        except Exception:
            redirect = reverse("horizon:admin:sla:index")
            exceptions.handle(self.request,
                              _("Unable to retrieve user roles."),
                              redirect=redirect)
        roles.sort(key=operator.attrgetter("id"))
        kwargs['roles'] = roles
        return kwargs

    def get_initial(self):
        # Set the domain of the user
        domain = api.keystone.get_default_domain(self.request)
        default_role = api.keystone.get_default_role(self.request)
        return {'domain_id': domain.id,
                'domain_name': domain.name,
                'role_id': getattr(default_role, "id", None)}


class LogDetailsView(forms.ModalFormMixin, tables.DataTableView):
    template_name = 'admin/sla/action_details.html'
    table_class = project_tables.SLALogsDetailsTable
    sla_logs_details = []
    def get_data(self):
        try:
            self.sla_logs_details = self_healing.get_sla_logs_details(self.kwargs['id'])
        except Exception:
            msg = _('Unable to get sla action logs details status.')
            exceptions.check_message(["Connection", "refused"], msg)

        return self.sla_logs_details

class GetTenantVmsView(generic_view):
    """
Required to update vms per tenant on ajax select-box change
#TODO(someone) Check if admin policy is being applied!
ONLY WORK FOR ACTIVE VM'S. IDEALLY STACTASH SHOULD RETURN THE LIsT
OF VM's recorded
"""

    def get(self, request, *args, **kwargs):
        #TODO(bug?) nova api ignore tenant_id

        tenant = kwargs.get('tenant_id')
        vms = []
        try:
            instances, more = api.nova.server_list(request,all_tenants=True)
            vms = dict((x.id, x.name) for x in instances
                          if x.tenant_id == tenant)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve vms.'))
        return HttpResponse(json.dumps(vms), content_type='text/json')


    #def dispatch(self, *args, **kwargs):
    #    return super(LogDetailsView, self).dispatch(*args, **kwargs)

    #def get_form_kwargs(self):
    #    kwargs = super(LogDetailsView, self).get_form_kwargs()
    #    try:
    #        roles = api.keystone.role_list(self.request)
    #    except Exception:
    #        redirect = reverse("horizon:admin:sla:index")
    #        exceptions.handle(self.request,
    #                          _("Unable to retrieve user roles."),
    #                          redirect=redirect)
    #    roles.sort(key=operator.attrgetter("id"))
    #    kwargs['roles'] = roles
    #    return kwargs

    #def get_initial(self):
    #    # Set the domain of the user
    #    domain = api.keystone.get_default_domain(self.request)
    #    default_role = api.keystone.get_default_role(self.request)
    #    return {'domain_id': domain.id,
    #            'domain_name': domain.name,
    #            'role_id': getattr(default_role, "id", None)}

#class AdminIndexView(tables.DataTableView):
#    table_class = project_tables.AdminInstancesTable
#    template_name = 'admin/instances/index.html'
#
#    def has_more_data(self, table):
#        return self._more
#
#    def get_data(self):
#        instances = []
#        marker = self.request.GET.get(
#            project_tables.AdminInstancesTable._meta.pagination_param, None)
#        try:
#            instances, self._more = api.nova.server_list(
#                self.request,
#                search_opts={'marker': marker,
#                             'paginate': True},
#                all_tenants=True)
#        except Exception:
#            self._more = False
#            exceptions.handle(self.request,
#                              _('Unable to retrieve instance list.'))
#        if instances:
#            # Gather our flavors to correlate against IDs
#            try:
#                flavors = api.nova.flavor_list(self.request)
#            except Exception:
#                # If fails to retrieve flavor list, creates an empty list.
#                flavors = []#
#
#            # Gather our tenants to correlate against IDs
#            try:
#                tenants, has_more = api.keystone.tenant_list(self.request)
#            except Exception:
#                tenants = []
#                msg = _('Unable to retrieve instance project information.')
#                exceptions.handle(self.request, msg)#
#
#            full_flavors = SortedDict([(f.id, f) for f in flavors])
#            tenant_dict = SortedDict([(t.id, t) for t in tenants])
#            # Loop through instances to get flavor and tenant info.
#            for inst in instances:
#                flavor_id = inst.flavor["id"]
#                try:
#                    if flavor_id in full_flavors:
#                        inst.full_flavor = full_flavors[flavor_id]
#                    else:
#                        # If the flavor_id is not in full_flavors list,
#                        # gets it via nova api.
#                        inst.full_flavor = api.nova.flavor_get(
#                            self.request, flavor_id)
#                except Exception:
#                    msg = _('Unable to retrieve instance size information.')
#                    exceptions.handle(self.request, msg)
#                tenant = tenant_dict.get(inst.tenant_id, None)
#               inst.tenant_name = getattr(tenant, "name", None)
#        return instances