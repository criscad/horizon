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

import logging

from django.forms import ValidationError  # noqa
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables  # noqa

from horizon import exceptions
from horizon import forms
from horizon.forms import fields as horizon_fields
from django.forms import widgets
from django.core import urlresolvers

from openstack_dashboard import api
from openstack_dashboard.openstack.common import jsonutils

LOG = logging.getLogger(__name__)


class BaseActionForm(forms.SelfHandlingForm):
    def __init__(self, request, *args, **kwargs):
        super(BaseActionForm, self).__init__(request, *args, **kwargs)

        # Populate project choices
        project_choices = []

        # If the user is already set (update action), list only projects which
        # the user has access to.
        user_id = kwargs['initial'].get('id', None)
        domain_id = kwargs['initial'].get('domain_id', None)
        projects, has_more = api.keystone.tenant_list(request,
                                                      domain=domain_id,
                                                      user=user_id)
        for project in projects:
            if project.enabled:
                project_choices.append((project.id, project.name))
        if not project_choices:
            project_choices.insert(0, ('', _("No available projects")))
        elif len(project_choices) > 1:
            project_choices.insert(0, ("All Projects", _("All Projects")))
            project_choices.insert(0, ('', _("Select a project")))
        self.fields['project'].choices = project_choices

    def clean(self):
        '''Check to make sure password fields match.'''
        data = super(forms.Form, self).clean()
        if 'password' in data:
            if data['password'] != data.get('confirm_password', None):
                raise ValidationError(_('Passwords do not match.'))
        return data


ADD_PROJECT_URL = "horizon:admin:projects:create"
ADD_ALARM_URL = "horizon:admin:alarms:create"


class CreateHealingActionForm(BaseActionForm):
    # Hide the domain_id and domain_name by default
    domain_id = forms.CharField(label=_("Domain ID"),
                                required=False,
                                widget=forms.HiddenInput())
    domain_name = forms.CharField(label=_("Domain Name"),
                                  required=False,
                                  widget=forms.HiddenInput())

    name = forms.CharField(label=_("Contract Name"),
                                  required=True)

    project = forms.DynamicChoiceField(label=_("Project"),
                                       add_item_link=ADD_PROJECT_URL)

    condition = forms.ChoiceField(label=_("Condition"),
                                  widget=forms.Select(attrs={
                                    'class': 'switchable',
                                    'data-slug': 'anaction'
                                  })
                                  )

    notification = forms.ChoiceField(label=_("Notification Type"),
                                     required=False)

    alarm = forms.DynamicChoiceField(label=_("Ceilometer Alarms"),
                                  required=False,
                                  initial='',
        widget=horizon_fields.DynamicSelectWidget(attrs={
            'class': 'switched',
            'data-switch-on': 'anaction',
            'data-anaction-ceilometer_external_resource': _("Ceilometer Alarms"),
        }),
        add_item_link=ADD_ALARM_URL
        )

    period_configuration = forms.CharField(label=_("Time Period configuration"),
                               required=False,
                               initial='60',
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'anaction',
            'data-anaction-host_down': _("Period (seconds)"),
            'data-anaction-vm_error': _("Period (seconds)"),
            'readonly': 'readonly'
        })
        )

    resource = forms.ChoiceField(label=_("Resource"),
                                 initial='',
                                 required=False,
        widget=forms.Select(attrs={
            'class': 'switched',
            'data-switch-on': 'anaction',
            'data-anaction-resource': _("Resource"),
            'data-anaction-ceilometer_external_resource': _("Resource"),
            'data-anaction-generic_script_alarm': _("Resource"),
            'data-anaction-notification_alarm': _("Resource"),
        })
        )

    action = forms.ChoiceField(label=_("Action"))


    action_options = forms.CharField(label=_("Action options"),
                                     required=False,
                                     initial='')


    def __init__(self, *args, **kwargs):
        roles = kwargs.pop('roles')
        super(CreateHealingActionForm, self).__init__(*args, **kwargs)

        condition_choices = [('host_down', 'Host Down'), ('vm_error', 'Vm Error'),
                             ('resource', 'Resource: Storage > 90%'),
                             ('ceilometer_external_resource', 'Ceilometer Alarm'), 
                             ('generic_script_alarm', 'External Alarm'),
                             # superseed by ceilometer sooner or later.
                             ('notification_alarm', 'Notification Alarm')]
        self.fields['condition'].choices = condition_choices

        self.fields['notification'].choices = [('compute.instance.create.end',
                                               _('Instance Launched'))]

        actions = api.self_healing.get_available_actions()
        action_choices = [] #[('evacuate', 'Evacuate all Host VMs'), ('reboot', 'Restart All VMs'), ('migrate', 'Migrate All VMs')]
        for x in actions:
            action_choices.append((x.name,x.description))
        self.fields['action'].choices = action_choices

        resources_choices = self._get_vm_resources()
        self.fields['resource'].choices = resources_choices

        alarm_choices = self._get_alarms()
        self.fields['alarm'].choices = alarm_choices

        # For keystone V3, display the two fields in read-only
        if api.keystone.VERSIONS.active >= 3:
            readonlyInput = forms.TextInput(attrs={'readonly': 'readonly'})
            self.fields["domain_id"].widget = readonlyInput
            self.fields["domain_name"].widget = readonlyInput

    def _get_vm_resources(self):
            servers = api.nova.server_list(self.request,all_tenants=True)
            vm_resources = [('','Select a resource')]
            if servers and servers[0]:
                r = range(0, servers[0].__len__(), 1)
                for i in r:
                    vm_resources.append((servers[0][i]._apiresource.id,
                                         servers[0][i]._apiresource.human_id))
            return vm_resources

    def _get_alarms(self):
            al = api.ceilometer.alarm_list(self.request)
            alarms_choices = [('','Select an alarm')]
            if al:
                r = range(0, al.__len__(), 1)
                for i in r:
                    name = al[i]._apiresource.human_id
                    if name == None:
                        name = al[i]._apiresource.alarm_id
                    alarms_choices.append((al[i]._apiresource.alarm_id,name))
            return alarms_choices

    # We have to protect the entire "data" dict because it contains the
    # password and confirm_password strings.
    @sensitive_variables('data')
    def handle(self, request, data):
        try:
            LOG.info('Creating a healing action.')

            project = ''
            if (data['project'] != 'All Projects'):
                project = data['project']

            if data['condition'].upper() == 'HOST_DOWN':
                new_action = api.self_healing.set_action_parameters(condition=data['condition'].upper(),
                                                                      action=data['action'],
                                                                      project=project,
                                                                      alarm_data=jsonutils.dumps({'period': data['period_configuration']}),
                                                                      action_options=jsonutils.dumps(data['action_options']),
                                                                      name=data['name']
                                                                    )
            elif data['condition'].upper() == 'VM_ERROR':
                new_action = api.self_healing.set_action_parameters(condition=data['condition'].upper(),
                                                                      action=data['action'],
                                                                      project=project,
                                                                      alarm_data=jsonutils.dumps({'period': data['period_configuration']}),
                                                                      action_options=jsonutils.dumps(data['action_options']),
                                                                      name=data['name']
                                                                    )
            elif data['condition'].upper() == 'CEILOMETER_EXTERNAL_RESOURCE':
                new_action = api.self_healing.set_action_parameters(condition=data['condition'].upper(),
                                                                      action=data['action'],
                                                                      project=project,
                                                                      resource_id=data['resource'],
                                                                      alarm_data=jsonutils.dumps({'alarm_id': data['alarm']}),
                                                                      action_options=jsonutils.dumps(data['action_options']),
                                                                      name=data['name']
                                                                    )
            elif data['condition'].upper() == 'GENERIC_SCRIPT_ALARM':
                new_action = api.self_healing.set_action_parameters(condition=data['condition'].upper(),
                                                                      action=data['action'],
                                                                      project=project,
                                                                      resource_id=data['resource'],
                                                                      action_options=jsonutils.dumps(data['action_options']),
                                                                      name=data['name']
                                                                    )
            elif data['condition'].upper() == 'RESOURCE':
                new_action = api.self_healing.set_action_parameters(condition=data['condition'].upper(),
                                                                      action=data['action'],
                                                                      project=project,
                                                                      resource_id=data['resource'],
                                                                      alarm_data=jsonutils.dumps({"period": 20, "threshold": "95", "operator": "gt", "meter": "disk.percentage"}),
                                                                      action_options=jsonutils.dumps(data['action_options']),
                                                                      name=data['name']
                                                                      )
            elif data['condition'].upper() == 'NOTIFICATION_ALARM':
                new_action = api.self_healing.set_action_parameters(condition=data['condition'].upper(),
                                                                      action=data['action'],
                                                                      project=project,
                                                                      resource_id=data['resource'],
                                                                      alarm_data=jsonutils.dumps({"meter": data['notification']}),
                                                                      action_options=jsonutils.dumps(data['action_options']),
                                                                      name=data['name']
                                                                      )
            #for creating an alarms template {"period": 20, "threshold": "100", "operator": "gt", "meter": "disk.read.bytes"}
            #form alarm_id {"alarm_id":"5f905ad6-c67a-4c6e-92bd-3fd179b5de42"}
            return new_action
        except Exception:
            exceptions.handle(request, _('Unable to create healing action.'))

    def clean(self):
        cleaned_data = super(CreateHealingActionForm, self).clean()
        condition = cleaned_data.get('condition')
        #action = cleaned_data.get("action")
        alarm = cleaned_data.get("alarm")
        resource = cleaned_data.get("resource")

        #if action != 'evacuate':
        #    msg = _('Action not available.')
        #    raise ValidationError(msg)
        if condition.upper() == 'CEILOMETER_EXTERNAL_RESOURCE' and alarm == '':
            msg = _('Please select an alarm.')
            raise ValidationError(msg)
        if resource == '' and condition.upper() not in ['HOST_DOWN', 'VM_ERROR',
                                                        'NOTIFICATION_ALARM']:
            msg = _('Please select a resource.')
            raise ValidationError(msg)

        return cleaned_data


class ActionDetailsForm(forms.SelfHandlingForm):
    # Hide the domain_id and domain_name by default

    def __init__(self, *args, **kwargs):
        roles = kwargs.pop('roles')
        super(ActionDetailsForm, self).__init__(*args, **kwargs)

    # We have to protect the entire "data" dict because it contains the
    # password and confirm_password strings.
    @sensitive_variables('data')
    def handle(self, request, data):
        pass

#class UpdateUserForm(BaseUserForm):
#    # Hide the domain_id and domain_name by default
#    domain_id = forms.CharField(label=_("Domain ID"),
#                                required=False,
#                                widget=forms.HiddenInput())
#    domain_name = forms.CharField(label=_("Domain Name"),
#                                  required=False,
#                                  widget=forms.HiddenInput())
#    id = forms.CharField(label=_("ID"), widget=forms.HiddenInput)
#    name = forms.CharField(label=_("User Name"))
#    email = forms.EmailField(
#        label=_("Email"),
#        required=False)
#    password = forms.RegexField(
#        label=_("Password"),
#        widget=forms.PasswordInput(render_value=False),
#        regex=validators.password_validator(),
#        required=False,
#        error_messages={'invalid': validators.password_validator_msg()})
#    confirm_password = forms.CharField(
#        label=_("Confirm Password"),
#        widget=forms.PasswordInput(render_value=False),
#        required=False)
#    project = forms.ChoiceField(label=_("Primary Project"))
#
#    def __init__(self, request, *args, **kwargs):
#        super(UpdateUserForm, self).__init__(request, *args, **kwargs)
#
#        if api.keystone.keystone_can_edit_user() is False:
#            for field in ('name', 'email', 'password', 'confirm_password'):
#                self.fields.pop(field)
#                # For keystone V3, display the two fields in read-only
#        if api.keystone.VERSIONS.active >= 3:
#            readonlyInput = forms.TextInput(attrs={'readonly': 'readonly'})
#            self.fields["domain_id"].widget = readonlyInput
#            self.fields["domain_name"].widget = readonlyInput
#
#    # We have to protect the entire "data" dict because it contains the
#    # password and confirm_password strings.
#    @sensitive_variables('data', 'password')
#    def handle(self, request, data):
#        user = data.pop('id')
#
#        # Throw away the password confirmation, we're done with it.
#        data.pop('confirm_password', None)
#
#        data.pop('domain_id')
#        data.pop('domain_name')
#
#        try:
#            response = api.keystone.user_update(request, user, **data)
#            messages.success(request,
#                             _('User has been updated successfully.'))
#        except Exception:
#            response = exceptions.handle(request, ignore=True)
#            messages.error(request, _('Unable to update the user.'))
#
#        if isinstance(response, http.HttpResponse):
#            return response
#        else:
#            return True
