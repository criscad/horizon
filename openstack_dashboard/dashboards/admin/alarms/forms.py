# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 NEC Corporation
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

import logging

from django.core.urlresolvers import reverse  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


LOG = logging.getLogger(__name__)

# TODO(lsmola) it's probably worth to make this a Workflow with
# metering tab, actions tab, options tab


class CreateAlarm(forms.SelfHandlingForm):
    failure_url = 'horizon:admin:alarms:index'

    name = forms.CharField(label=_("Name"))
    description = forms.CharField(label=_("Description"),
                                  widget=forms.Textarea())
    project_id = forms.ChoiceField(label=_("Project"))
    enabled = forms.BooleanField(label=_("enabled"),
                                 initial=True, required=False)
    repeat_actions = forms.BooleanField(label=_("Repeat Actions"),
                                        initial=False, required=False)
    evaluation_periods = forms.CharField(label=_("Evaluation Periods"),
                                         initial=2)
    meter_name = forms.CharField(label=_("Meter"),
                                 initial="storage.objects")
    comparison_operator = forms.CharField(label=_("Comparison Operator"),
                                          initial="gt")
    threshold = forms.CharField(label=_("Threshold"),
                                initial=200)
    period = forms.CharField(label=_("Period"),
                             initial=240)
    statistic = forms.CharField(label=_("Statistic"),
                                initial='avg')
    alarm_actions = forms.CharField(label=_("Alarm actions"),
                                    initial='http://site:8000/alarm')
    insufficient_data_actions = forms.CharField(
        label=_("Insufficient data actions"),
        initial='http://site:8000/alarm')
    ok_actions = forms.CharField(label=_("Ok actions"),
                                 initial='http://site:8000/alarm')

    # TODO(lsmola) manually change state? seems it is possible.
    # state = forms.CharField(label=_("State"),
    #                        initial='ok')

    # TODO(lsmola) this could be used to categorize the alarms
    # "matching_metadata": {
    #    "key_name": "key_value"
    #},

    def __init__(self, request, *args, **kwargs):
        super(CreateAlarm, self).__init__(request, *args, **kwargs)
        # TODO(lsmola) wait for result of this bug
        # https://bugs.launchpad.net/ceilometer/+bug/1223829

        tenant_choices = [('', _("Select a project"))]
        tenants, has_more = api.keystone.tenant_list(request)
        for tenant in tenants:
            if tenant.enabled:
                tenant_choices.append((tenant.id, tenant.name))
        self.fields['project_id'].choices = tenant_choices

    def clean(self):
        self.cleaned_data['ok_actions'] =\
            self.cleaned_data.get('ok_actions', "").split(",")
        self.cleaned_data['alarm_actions'] =\
            self.cleaned_data.get('alarm_actions', "").split(",")
        self.cleaned_data['insufficient_data_actions'] =\
            self.cleaned_data.get('insufficient_data_actions', "").split(",")
        return self.cleaned_data

    def handle(self, request, data):
        try:
            LOG.debug('params = %s' % data)

            alarm = api.ceilometer.alarm_create(request,
                                                **data)
            msg = (_('Alarm %s was successfully created.') %
                   alarm.id)
            LOG.debug(msg)
            messages.success(request, msg)
            return alarm
        except Exception:
            msg = _('Failed to create alarm')
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)


class UpdateAlarm(CreateAlarm):
    name = forms.CharField(label=_("Name"),
                           widget=forms.HiddenInput())
    failure_url = 'horizon:admin:alarms:detail'

    def handle(self, request, data):
        try:
            LOG.debug('params = %s' % data)
            alarm = api.ceilometer.alarm_update(request,
                                                self.initial['alarm_id'],
                                                **data)
            msg = (_('Alarm %s was successfully updated.') %
                   self.initial['alarm_id'])
            LOG.debug(msg)
            messages.success(request, msg)
            return alarm
        except Exception:
            msg = _('Failed to update alarm %s') % data['port_id']
            LOG.info(msg)
            redirect = reverse(self.failure_url,
                               args=[self.initial['alarm_id']])
            exceptions.handle(request, msg, redirect=redirect)
