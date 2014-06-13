__author__ = 'cfiorent'

from healingclient.api import client
from healingclient.api.slacontract import SLAContractManager
from healingclient.api.tracking import TrackingManager
from healingclient.api.actions import ActionManager
from openstack_dashboard.openstack.common import jsonutils


aclient = client.Client()
SLAManager = SLAContractManager(aclient)
ActionManager = ActionManager(aclient)
TrackingManager = TrackingManager(aclient)


def set_action_parameters(condition, action, project, period):
    an_sla_contract = SLAManager.create(project_id=project, type=condition, value=None, action=action,
               alarm_data=jsonutils.dumps({'period': period}), resource_id=None)

    #a = HealingAction()
    #a.condition = an_sla_contract.type
    #a.action = an_sla_contract.action
    #a.project = an_sla_contract.tenant_id
    #a.alarm_data = jsonutils.dumps({'period': '60'})
    #a.id = an_sla_contract.id
    return an_sla_contract

    ### mock ###
    #id[0] = id[0] +1
    #a = HealingAction()
    #a.condition = condition
    #a.action = action
    #a.project = project
    #a.period = period
    #a.id = id[0]
    #actions.append(a)
    #return a

def delete_action_parameters(id):
    contract_list = SLAManager.delete(id)
    return contract_list

    ### mock ###
    #actions.pop(int(id))
    #return actions

def get_action_parameters():
    contract_list = SLAManager.list()
    actions_list = []
    for c in contract_list:
        a = HealingAction()
        a.condition = c.type
        a.action = c.action
        a.project = c.project_id
        #a.period = '60' #c.alarm_data['period']
        a.id = c.id
        actions_list.append(a)
    return actions_list

    ### mock ###
    #return actions

##############################

class HealingAction():
    condition = ''
    action = ''
    project = ''
    period =''
    id = ''


### mock actions###
#global actions
#actions= []
#global id
#id = []
#id.append(int(0))

##############################

### mock resources status###

#def get_vm_resources_status():
#    return [VMResources(id='1', project='Project 1', vm='VM 1', host= 'Host 1', status='ACTIVE'),VMResources(id='2', project='Project 1', vm='VM 2', host= 'Host 1',status='SHUT DOWN')]
#
#class VMResources():
#    status = 'active'
#    project = 'project 1'
#    host = 'host 1'
#    vm ='vm1'
#    id = '1'
#    def __init__(self, id, project, vm, host, status):
#        self.status = status
#        self.project = project
#        self.host = host
#        self.vm = vm
#        self.id = id
#
#def get_host_resources_status():
#    return [HostResources(id='1', host='Host 1', status='ACTIVE')]
#
#class HostResources():
#    status = 'active'
#    host ='host1'
#    id = '1'
#    def __init__(self, id, host, status):
#        self.status = status
#        self.host = host
#        self.id = id


def get_sla_logs():
    ###mock###
    #return [SLALogs(id='0', date='05:10:2014:15:40', resource='Host 1', alarm='Host Down'), SLALogs(id='1', date='05:10:2014:15:24', resource='Host 1', alarm='Evacuated')]

    sla_logs = TrackingManager.list()
    sla_logs_list = []
    for c in sla_logs:
        a = SLALogs(date = c.time[0:19], resources = c.data, alarm = c.alarm_id, id = c.id)
        sla_logs_list.append(a)
    return sla_logs_list

#def map_list(ll):
#    s = ''
#    l = list(map(str, ll))
#    for c in l:
#        s = s + c + ' '
#    return s

class SLALogs():
    date = '1/1/1'
    resources ='host1'
    alarm = 'Host Down'
    id = 1
    def __init__(self, id, date, resources, alarm):
        self.date = date
        self.resources = resources
        self.id = id
        self.alarm = alarm


def get_sla_logs_details(log_id):
    ###mock###
    #return [SLALogsDetails(id='0', date='05:10:2014:15:40', action='Evacuation', details='Tried'), SLALogsDetails(id='1', date='05:10:2014:15:24', action='Evacuation', details='Retry')]

    sla_logs_details = ActionManager.list(request_id=log_id)
    sla_logs_details_list = []
    for c in sla_logs_details:
        a = SLALogsDetails(date = c.created_at[0:19], action = c.name, status = c.status, output = c.output, target_id = c.target_id, id = c.id)
        sla_logs_details_list.append(a)
    return sla_logs_details_list

class SLALogsDetails():
    date = ''
    action =''
    status = ''
    output = ''
    target_id = ''
    id = ''
    def __init__(self, id, date, action, status, output, target_id):
        self.date = date
        self.action = action
        self.id = id
        self.status = status
        self.output = output
        self.target_id = target_id
