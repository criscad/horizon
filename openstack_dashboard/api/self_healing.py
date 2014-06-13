__author__ = 'cfiorent'

from healingclient.api import client
from healingclient.api.slacontract import SLAContractManager
from healingclient.api.tracking import TrackingManager
from healingclient.api.actions import ActionManager
from healingclient.api.handlers import HandlerManager


aclient = client.Client()
SLAManager = SLAContractManager(aclient)
ActionManager = ActionManager(aclient)
TrackingManager = TrackingManager(aclient)
HandlerManager = HandlerManager(aclient)


def set_action_parameters(condition, action, project, resource_id = None, value = None, alarm_data= None):
    an_sla_contract = SLAManager.create(project_id=project, type=condition, action=action,
               alarm_data=alarm_data, resource_id=resource_id, value = value)

    return an_sla_contract

def delete_action_parameters(id):
    contract_list = SLAManager.delete(id)
    return contract_list


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

class HealingAction():
    condition = ''
    action = ''
    project = ''
    period =''
    id = ''


def get_available_actions():
    actions = HandlerManager.list()
    return actions


def get_sla_logs():

    sla_logs = TrackingManager.list()
    sla_logs_list = []
    for c in sla_logs:
        a = SLALogs(date = c.time[0:19], resources = c.data, alarm = c.alarm_id, id = c.id)
        sla_logs_list.append(a)
    return sla_logs_list

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
