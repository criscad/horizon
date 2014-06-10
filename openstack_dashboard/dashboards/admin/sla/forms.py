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
from django import http
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables  # noqa

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import validators

from openstack_dashboard.dashboards.admin.sla import tables

from openstack_dashboard import api


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


class CreateHealingActionForm(BaseActionForm):
    # Hide the domain_id and domain_name by default
    domain_id = forms.CharField(label=_("Domain ID"),
                                required=False,
                                widget=forms.HiddenInput())
    domain_name = forms.CharField(label=_("Domain Name"),
                                  required=False,
                                  widget=forms.HiddenInput())

    project = forms.DynamicChoiceField(label=_("Project"),
                                       add_item_link=ADD_PROJECT_URL)

    condition = forms.ChoiceField(label=_("Condition"),
                                  widget=forms.Select(attrs={
                                    'class': 'switchable',
                                    'data-slug': 'anaction'}))

    host_down_configuration = forms.CharField(label=_("Host Down configuration"),
                               required=False,
                               initial='60',
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'anaction',
            'data-anaction-host_down': _("Period (seconds)"),
            'readonly': 'readonly'
        })
        )

    period = forms.ChoiceField(label=_("Period (seconds)"),
                               required=False,
                               initial='60',
        widget=forms.Select(attrs={
            'class': 'switched',
            'data-switch-on': 'anaction',
            'data-anaction-vm_down': _("Period (seconds)"),
            'data-anaction-services_down': _("Period (seconds)")
        }))

    action = forms.ChoiceField(label=_("Action"))



    def __init__(self, *args, **kwargs):
        roles = kwargs.pop('roles')
        super(CreateHealingActionForm, self).__init__(*args, **kwargs)

        #instance_id = kwargs.get('initial', {}).get('instance_id')
        #self.fields['instance_id'].initial = instance_id
        condition_choices = [('host_down', 'Host Down'), ('vm_down', 'VM Down'), ('services_down', 'OS Services Down')]
        self.fields['condition'].choices = condition_choices
        #TODO call api for action, called handlerlist
        action_choices = [('evacuate', 'Evacuate all Host VMs'), ('reboot', 'Restart All VMs'), ('migrate', 'Migrate All VMs')]
        self.fields['action'].choices = action_choices
        period_choices = [('60', '60'), ('120', '120')]
        self.fields['period'].choices = period_choices
        #self.fields['evacuate_notes'].TextInput = 'lalala'

        # For keystone V3, display the two fields in read-only
        if api.keystone.VERSIONS.active >= 3:
            readonlyInput = forms.TextInput(attrs={'readonly': 'readonly'})
            self.fields["domain_id"].widget = readonlyInput
            self.fields["domain_name"].widget = readonlyInput


    # We have to protect the entire "data" dict because it contains the
    # password and confirm_password strings.
    @sensitive_variables('data')
    def handle(self, request, data):
        try:
            LOG.info('Creating a healing action.')
            condition = data['condition'].upper()
            if (data['project'] != 'All Projects'):
                new_action = api.self_healing.set_action_parameters(condition=condition,
                                                                  action=data['action'],
                                                                  project=data['project'],
                                                                  period=data['period'])
                return new_action
            else:
                #l = range(2, self.fields['project'].choices.__len__(), 1)
                #for i in l:
                #    p = self.fields['project'].choices[i]
                #    new_action = api.self_healing.set_action_parameters(condition=data['condition'],
                #                                                  action=data['action'],
                #                                                  project=p[0],
                #                                                  period=data['period'])


                new_action = api.self_healing.set_action_parameters(condition=condition,
                                                                  action=data['action'],
                                                                  project='',
                                                                  period=data['period'])
                return new_action
        except Exception:
            exceptions.handle(request, _('Unable to create healing action.'))


    def clean(self):
        cleaned_data = super(CreateHealingActionForm, self).clean()

        condition = cleaned_data.get('condition')
        action = cleaned_data.get("action")

        if condition.upper() != 'HOST_DOWN':
            msg = _('Condition not available.')
            raise ValidationError(msg)
        if action != 'evacuate':
            msg = _('Action not available.')
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
