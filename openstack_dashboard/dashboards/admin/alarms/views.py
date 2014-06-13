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
from django.core.urlresolvers import reverse_lazy  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import forms
from horizon import tabs

from openstack_dashboard import api

from openstack_dashboard.dashboards.admin.alarms import tabs as \
    alarm_tabs

from openstack_dashboard.dashboards.admin.alarms \
    import forms as alarm_forms

LOG = logging.getLogger(__name__)


class IndexView(tabs.TabbedTableView):
    tab_group_class = alarm_tabs.AlarmManagementTabs
    template_name = 'admin/alarms/index.html'


class DetailView(tabs.TabView):
    template_name = 'admin/alarms/detail.html'
    failure_url = reverse_lazy('horizon:admin:alarms:index')

    def _get_data(self):
        if not hasattr(self, "_alarm"):
            try:
                alarm_id = self.kwargs['alarm_id']
                alarm = api.neutron.alarm_get(self.request, alarm_id)
                alarm.set_id_as_name_if_empty(length=0)
            except Exception:
                redirect = self.failure_url
                exceptions.handle(self.request,
                                  _('Unable to retrieve details for '
                                    'alarm "%s".') % alarm_id,
                                    redirect=redirect)
            self._alarm = alarm
        return self._alarm

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context["alarm"] = self._get_data()
        return context


class CreateView(forms.ModalFormView):
    form_class = alarm_forms.CreateAlarm
    template_name = 'admin/alarms/create.html'
    success_url = reverse_lazy('horizon:admin:alarms:index')

    def get_initial(self):
        initial = {}
        # TODO(lsmola) These are getting automatically set on the
        # Ceilometer side, figure out, whether we need to set the
        # default value here.
        # initial['project_id'] = self.request.user.tenant_id
        # initial['user_id'] = self.request.user.id
        return initial


class UpdateView(forms.ModalFormView):
    form_class = alarm_forms.UpdateAlarm
    template_name = 'admin/alarms/update.html'
    success_url = reverse_lazy('horizon:admin:alarms:index')

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            alarm_id = self.kwargs['alarm_id']
            try:
                self._object = api.ceilometer.alarm_get(self.request, alarm_id)
            except Exception:
                redirect = reverse("horizon:admin:alarms:index")
                msg = _('Unable to retrieve alarm details.')
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_initial(self):
        alarm = self._get_object()
        initial = super(UpdateView, self).get_initial()
        visible_attrs = ('alarm_actions', 'alarm_id', 'comparison_operator',
                         'description', 'enabled', 'evaluation_periods',
                         'insufficient_data_actions', 'matching_metadata',
                         'meter_name', 'name', 'ok_actions', 'period',
                         'project_id', 'repeat_actions', 'state',
                         'state_timestamp', 'statistic', 'threshold',
                         'timestamp', 'user_id')
        for attr in visible_attrs:
            initial[attr] = getattr(alarm, attr, None)

        initial['ok_actions'] = ",".join(initial['ok_actions'])
        initial['alarm_actions'] = ",".join(initial['alarm_actions'])
        initial['insufficient_data_actions'] = (
            ",".join(initial['insufficient_data_actions']))

        return initial
