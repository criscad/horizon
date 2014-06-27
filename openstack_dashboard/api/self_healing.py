__author__ = 'cfiorent'

from healingclient.api import client
from healingclient.api.slacontract import SLAContractManager
from healingclient.api.tracking import TrackingManager
from healingclient.api.actions import ActionManager
from healingclient.api.handlers import HandlerManager
from healingclient.api.slastatistics import SLAStatisticsManager


aclient = client.Client()
SLAManager = SLAContractManager(aclient)
ActionManager = ActionManager(aclient)
TrackingManager = TrackingManager(aclient)
HandlerManager = HandlerManager(aclient)
SLAStatisticsManager = SLAStatisticsManager(aclient)

import json
def set_action_parameters(condition, action, project, name, resource_id=None, value=None, alarm_data=None,
                          action_options=None):
    if action_options:
        try:
            action_options = json.loads(action_options)
        except:
            action_options = None
            
    an_sla_contract = SLAManager.create(name=name, project_id=project, type=condition, action=action,
                                        alarm_data=alarm_data, resource_id=resource_id, value=value,
                                        action_options=action_options)

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
        a.name = c.name
        actions_list.append(a)
    return actions_list

class HealingAction():
    condition = ''
    action = ''
    project = ''
    period =''
    id = ''
    name =''


def get_available_actions():
    actions = HandlerManager.list()
    return actions


def get_sla_logs():
    sla_logs = TrackingManager.list() or []
    return sla_logs


def get_sla_logs_details(log_id):
    sla_logs_details = ActionManager.list(request_id=log_id)
    return sla_logs_details or []


def get_sla_statistics(stat_type, project_id, from_date, to_date,
            resource_id=None):
    sla_statistics = [(SLAStatisticsManager.get(stat_type=stat_type, project_id=project_id,
                                              from_date=from_date, to_date=to_date, resource_id=resource_id))]
    return sla_statistics or []