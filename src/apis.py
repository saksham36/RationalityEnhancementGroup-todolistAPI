import numpy as np
import pandas as pd
import json
from src.utils import tree_to_old_structure
from todolistMDP.mdp_solvers \
    import backward_induction, policy_iteration, value_iteration
from todolistMDP.to_do_list import *
from src.utils import task_list_from_projects


def assign_constant_points(projects, default_task=10):
    '''
    Takes in parsed project tree, with one level of tasks
    Outputs project tree with constant points assigned
    '''
    for goal in projects:
        for child in goal["ch"]:
            child["val"] = default_task
    return projects


def assign_random_points(projects, distribution_fxn = np.random.normal, fxn_args = (10,2)):
    '''
    Takes in parsed project tree, with one level of tasks
    Outputs project tree with random points assigned according to distribution function with inputted args
    '''
    for goal in projects:
        for child in goal["ch"]:
            child["val"] = distribution_fxn(*fxn_args)
    return projects
    
    
def assign_hierarchical_points(projects):
    raise NotImplementedError


def assign_old_api_points(projects, solver_fn, duration=8*60):
    '''
    input: parsed project tree, duration of current day, and planning function
    output: task list of tasks to be done that day (c.f. shedulers.py)

    The provided solver function creates an ToDoListMDP object and solves the
    MDP. Possible solver functions (so far):
        - backward_induction
        - policy_iteration
        - value_iteration
    '''

    old_structure = tree_to_old_structure(projects, duration)
    to_do_list = ToDoList(old_structure,start_time=0, non_goal_tasks=[])
    mdp = solver_fn(to_do_list)
    mdp.scale_rewards()

    
    actions_and_rewards = []
    task_list = task_list_from_projects(projects)
    tasks = mdp.to_do_list.get_tasks()
    today_tasks = [task["id"] for task in task_list if task["today"] == 1]

    state = (tuple(0 for task in mdp.get_tasks_list()),0) #starting state
    #first schedule today tasks
    for today_task in today_tasks:
        action = next(item for item in mdp.get_possible_actions(state) if (today_task == tasks[item].description))
        next_state_and_prob = mdp.get_trans_states_and_probs(state, action)
        next_state = next_state_and_prob[0][0]
        duration -= next_state[1]
        reward = mdp.get_expected_pseudo_rewards(state, possible_action, transformed = False)
        state = next_state
        actions_and_rewards.append((action, reward))

    #then schedule based on mdp
    still_scheduling = True
    while still_scheduling:
        still_scheduling = False
        possible_actions = mdp.get_possible_actions(state)
        q_values = [mdp.get_q_value(state, action, mdp.V_states) for action in possible_actions]
        for action_index in np.argsort(q_values)[::-1]: #go through possible actions in order of q values
            possible_action = possible_actions[action_index]
            next_state_and_prob = mdp.get_trans_states_and_probs(state, possible_action)
            next_state = next_state_and_prob[0][0]
            
            if (duration-next_state[1])>=0: #see if the next best action would fit into that day's duration
                duration -= next_state[1]
                reward = mdp.get_expected_pseudo_rewards(state, possible_action, transformed = False)
                state = next_state
                still_scheduling = True
                actions_and_rewards.append((possible_action, reward))
                break  
    

    final_tasks = []
    for action, reward in actions_and_rewards:
        final_tasks.append((next(item for item in task_list if (item["id"] == tasks[action].description))))
        final_tasks[-1]["val"] = reward



    return final_tasks


def assign_length_points(projects):
    '''
    Takes in parsed and flattened project tree
    Outputs project tree with points assigned according to length heuristic
    '''
    for goal in projects:
        value_per_minute = goal["value"]/float(sum([child["est"] for child in goal["ch"]]))
        for child in goal["ch"]:
            child["val"] = child["est"]/float(value_per_minute)
    return projects


def get_actions_and_rewards(mdp, verbose=False):
    policy = mdp.get_optimal_policy()
    values = mdp.get_value_function()
    
    state = sorted(list(policy.keys()))[0]
    vec, tm = state
    
    value, action = values[state]
    
    if verbose:
        print(state, action, value)
    actions_and_rewards = [(action, value)]
    
    while policy[state] is not None:
        # Get task
        idx = policy[state]
        task = mdp.index_to_task[idx]
        
        # Get next state
        next_vec = list(vec)
        next_vec[idx] = 1
        
        tm += task.get_time_est()
        state = (tuple(next_vec), tm)
        vec, tm = state
    
        if verbose:
            print(state, action, value)
        actions_and_rewards += [(action, value)]
    
    return actions_and_rewards