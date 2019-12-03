import numpy as np

from to_do_list import ToDoListMDP
from numpy import linalg as LA


# ===== Backward Induction =====
def backward_induction(to_do_list):
    """
    Converts a given ToDoList to TodoListMDP and performs backward induction in
    order to find the optimal policy.
    
    Args:
        to_do_list: ToDoListMDP

    Returns:
        ToDoListMDP
    """
    mdp = ToDoListMDP(to_do_list)
    
    mdp.linearized_states = mdp.get_linearized_states()
    mdp.V_states = {}  # state --> (value, action)
    
    for state in mdp.linearized_states:
        mdp.V_states[state] = (0, None)  # state --> (value, action)
    
    # Perform Backward Iteration (Value Iteration 1 Time)
    for state in mdp.linearized_states:
        mdp.V_states[state] = mdp.get_value_and_action(state, mdp.V_states)
    
    mdp.optimal_policy = {}
    for state in mdp.V_states:
        mdp.optimal_policy[state] = mdp.V_states[state][1]
    
    # mdp.calculate_pseudo_rewards()
    # mdp.transform_pseudo_rewards()
    
    return mdp


# ===== Policy iteration =====
def policy_iteration(to_do_list):
    """
    Converts a given ToDoList to TodoListMDP and performs policy iteration in
    order to find the optimal policy.

    Args:
        to_do_list: ToDoListMDP

    Returns:
        ToDoListMDP
    """
    mdp = ToDoListMDP(to_do_list)

    new_policy = {}
    states = mdp.get_states()
    
    # Create initial policies
    for state in states:
        tasks = state[0]
        
        # Set initial policy of each state to the first possible action
        # (index of first 0)
        if 0 in tasks:
            new_policy[state] = tasks.index(0)
        else:
            new_policy[state] = 0
    
    n = len(states)
    empty_A = np.zeros((n, n))
    empty_b = np.zeros((n, 1))
    
    iterations = 0
    # Repeat until policy converges
    while mdp.optimal_policy != new_policy:
        iterations += 1
        print('Iteration', iterations)
        
        mdp.optimal_policy = new_policy
        mdp.V_states = policy_evaluation(mdp, mdp.optimal_policy,
                                         empty_A, empty_b)
        new_policy = policy_extraction(mdp, mdp.V_states)
    
    start_state = mdp.get_start_state()
    state = start_state
    optimal_tasks = []
    
    while not mdp.is_terminal(state):
        optimal_action = mdp.optimal_policy[state]
        task = mdp.get_tasks_list()[optimal_action]
        next_state_tasks = list(state[0])[:]
        next_state_tasks[optimal_action] = 1
        next_state = (tuple(next_state_tasks), state[1] + task.get_time_est())
        state = next_state
        optimal_tasks.append(task)
    
    # optimal_policy = [task.get_description() for task in optimal_tasks]

    return mdp


def policy_evaluation(mdp, policies, empty_A, empty_b):
    """
    given an MDP and a policy dictionary (from policy improvement)
    returns the V states for that policy for each state.
    v_states: state --> (state_value, action)
    """
    gamma = mdp.get_gamma()
    states = mdp.get_states()
    
    A = empty_A
    b = empty_b
    
    for i in range(len(states)):
        state = states[i]
        action = policies[state]
        A[i][i] = -1
        
        for next_state, prob in mdp.get_trans_states_and_probs(state, action):
            reward = mdp.get_reward(state, action, next_state)
            j = states.index(next_state)
            
            A[i][j] = gamma * prob
            b[i] = b[i] - prob * reward
    
    v = LA.solve(A, b)
    
    return {state: value for (state, value) in zip(states, v)}


def policy_extraction(mdp, v_states):
    """
    given an MDP and V_states (from policy evaluation)
    returns the optimal policy (policy is dictionary{states: action index})
    """
    # For every state, pick the action corresponding to the highest Q-value
    return {state: mdp.get_value_and_action(state, v_states)[1]
            for state in mdp.get_states()}


# ===== Value iteration =====
def value_iteration(to_do_list, epsilon=0.1):
    """
    Converts a given ToDoList to TodoListMDP and performs backward induction in
    order to find the optimal policy.

    Args:
        to_do_list: ToDoListMDP
        epsilon: Convergence condition value

    Returns:
        ToDoListMDP
    """
    mdp = ToDoListMDP(to_do_list)
    
    mdp.V_states = {state: (0, None)
                for state in mdp.get_states()}
    
    # Perform value iteration
    converged = False
    iterations = 0
    
    while not converged:
        iterations += 1
        print('Iteration', iterations)
        
        converged = True
        next_v_states = {}

        for state in mdp.V_states:
            next_v_states[state] = mdp.get_value_and_action(state, mdp.V_states)
            old_state_value = mdp.V_states[state][0]
            new_state_value = next_v_states[state][0]
            
            # Check convergence
            if abs(old_state_value - new_state_value) > epsilon:
                converged = False
                
        mdp.V_states = next_v_states

    # Extract optimal policy
    mdp.optimal_policy = policy_extraction(mdp, mdp.V_states)

    # Use pseudo-rewards
    # mdp.calculate_pseudo_rewards(v_states)
    # mdp.transform_pseudo_rewards()

    # Return MDP
    return mdp
