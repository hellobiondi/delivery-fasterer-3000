# from IPython.core.debugger import set_trace
import copy
from functools import wraps
import time as timer 
from Variables import SIMTIME_RATIO

import random 
random.seed(123)


def op_wrapper(operator):
    @wraps(operator)
    def wrap(*args, **kwargs):
        copied = args[0].copy()
        newGsp = operator(copied, args[1], **kwargs)
        return newGsp

    return wrap


@op_wrapper
def random_destroy(current, random_state):
    # choose 1 ID
    chosen_idx = random_state.randint(len(current.assigned))

    # remove from rider
    current.remove_job(current.assigned[chosen_idx].id)

    return current

@op_wrapper
def random_destroy_multi(current, random_state):
    
    deg = 0.1 
    num_to_destroy = int(len(current.assigned) * deg)
    
    for _ in range(num_to_destroy):
        # choose 1 ID
        chosen_idx = random_state.randint(len(current.assigned))

        # remove from rider
        current.remove_job(current.assigned[chosen_idx].id)
        
    return current

@op_wrapper
def random_destroy_lowest_pay(current, random_state):
    # sort the current assigned with lowest pay at the front 
    current.assigned = sorted(current.assigned, key=lambda x: x.pay, reverse = False)
    
    total = len(current.assigned)
    upper = int(0.2*total)
    
    if upper > 1: 
        random_select = random.sample(range(upper), 1)

        # choose 1 ID
        chosen_id = current.assigned[random_select[0]].id
        # remove from rider
        current.remove_job(chosen_id)

    return current


@op_wrapper
def random_repair(destroyed, random_state):
    """
    repairs with slots that picks up on time within the window of 15 mins  
    repairs random job arrangement 
    """
    # randomise the copied task list
    random_state.shuffle(destroyed.unassigned)
 
    for job in destroyed.unassigned:
        possible_slots = destroyed.get_possible_slots(job)
        
        if len(possible_slots) > 1:
            pickup_idx = random_state.randint(len(possible_slots) - 1)
            delivery_idx = random_state.randint(pickup_idx + 1, len(possible_slots))
            # try to assign the job
            result = destroyed.can_assign(job, possible_slots[pickup_idx], possible_slots[delivery_idx])
            # assign if possible
            if result:
                destroyed.assign_job(job, possible_slots[pickup_idx], possible_slots[delivery_idx])

    return destroyed


@op_wrapper
def random_repair_on_time(destroyed, random_state):
    """
    repairs with slots that picks up on time within the window of 15 mins  
    repairs with slots that picks up on time without penalty    
    """
    # randomise the copied task list
    random_state.shuffle(destroyed.unassigned)

    for job in destroyed.unassigned:
        # get the possible slots 
        possible_slots = destroyed.get_possible_slots(job)
        
         # sort the slots 
        possible_slots = sorted(possible_slots)
            
        # pick the good starting range  
        start_range = 0
        for x in range(len(possible_slots)):
            if possible_slots[x] <= job.pickup_time + 15: 
                start_range = x
            else:
                break 
                
        # pick the good ending range  
        end_range = 0
        for x in range(len(possible_slots)):
            if possible_slots[x] <= job.delivery_time: 
                end_range = x
            else:
                break 
        
        if len(possible_slots) > 1 and start_range > 1 and start_range < end_range-1:
            
            # pick a random start slot within the window 
            pickup_idx = random_state.randint(start_range - 1)
            delivery_idx = random_state.randint(pickup_idx + 1, end_range)

            # try to assign the job with the exact desired end slot 
            result = destroyed.can_assign(job, possible_slots[pickup_idx], possible_slots[delivery_idx])
            
            # assign if possible
            if result:
                destroyed.assign_job(job, possible_slots[pickup_idx], possible_slots[delivery_idx])

    return destroyed

@op_wrapper
def random_repair_best_pay(destroyed, random_state):
    """
    repairs with high pay jobs at the top 
    repairs with starting slots within acceptable 15mins window 
    """
    
    # sort the jobs with most profitable on top 
    destroyed.unassigned = sorted(destroyed.unassigned, key=lambda x: x.pay, reverse = True)
 
    for job in destroyed.unassigned:
        # get the possible slots 
        possible_slots = destroyed.get_possible_slots(job)
        
         # sort the slots 
        possible_slots = sorted(possible_slots)
            
        # pick the good starting range  
        start_range = 0
        for x in range(len(possible_slots)):
            if possible_slots[x] <= job.pickup_time + 15: 
                start_range = x
            else:
                break 
        
        if len(possible_slots) > 1 and start_range > 1:
            
            # pick a random start slot within the window 
            pickup_idx = random_state.randint(start_range - 1)
            delivery_idx = random_state.randint(pickup_idx + 1, len(possible_slots))

            # try to assign the job with the exact desired end slot 
            result = destroyed.can_assign(job, possible_slots[pickup_idx], possible_slots[delivery_idx])
            
            # assign if possible
            if result:
                destroyed.assign_job(job, possible_slots[pickup_idx], possible_slots[delivery_idx])

    return destroyed

@op_wrapper
def repair_long(destroyed, random_state):
    """
    repairs with high pay jobs at the top 
    repairs with starting slots within acceptable 15mins window 
    """
    
    # sort the jobs with most profitable on top 
    destroyed.unassigned = sorted(destroyed.unassigned, key=lambda x: x.pickup_loc[1], reverse = True)
 
    for job in destroyed.unassigned:
        # get the possible slots 
        possible_slots = destroyed.get_possible_slots(job)
        
         # sort the slots 
        possible_slots = sorted(possible_slots)
            
        # pick the good starting range  
        start_range = 0
        for x in range(len(possible_slots)):
            if possible_slots[x] <= job.pickup_time + 15: 
                start_range = x
            else:
                break 
        
        if len(possible_slots) > 1 and start_range > 1:
            
            # pick a random start slot within the window 
            pickup_idx = random_state.randint(start_range - 1)
            delivery_idx = random_state.randint(pickup_idx + 1, len(possible_slots))

            # try to assign the job with the exact desired end slot 
            result = destroyed.can_assign(job, possible_slots[pickup_idx], possible_slots[delivery_idx])
            
            # assign if possible
            if result:
                destroyed.assign_job(job, possible_slots[pickup_idx], possible_slots[delivery_idx])

    return destroyed

################################################################
#dynamic
################################################################
@op_wrapper
def dynamic_random_destroy(current, random_state):
    # choose 1 ID
    if len(current.assigned) > 0:
        # get a random idx 
        chosen_idx = random_state.randint(len(current.assigned))
        # get the job ID of the chosen job to remove 
        job_id = current.assigned[chosen_idx].id
        # get the current schedule of the chosen job 
        schedule_time = [x[0] for x in current.rider.schedule.items() if x[1][1] == job_id]
        
        # check of the job can be removed, if shift has started, past jobs cannot be shifted
        if current.shift_started_at is not None:
            now = timer.time_ns() // 1000000
            elapsed = (now - current.shift_started_at) / SIMTIME_RATIO
            if min(schedule_time) - 20 < elapsed:
                # unable to destroy, just return the current state 
                return current
        
        # get the id of the new jobs 
        new_id_list = [x.id for x in current.dynamic_jobs]
        # if the chosen job is not part of the new comers, we add them to our mandatory prev_assigned list 
        if job_id not in new_id_list:
            # we use this list as an extra helper list to easily identify those belonging to previous solution 
            current.prev_assigned.append([current.assigned[chosen_idx], schedule_time[0], schedule_time[1]])


        # remove from rider
        current.remove_job(current.assigned[chosen_idx].id)

    return current


@op_wrapper
def dynamic_random_repair(destroyed, random_state):
    """
    repairs by randomly arranging the jobs instead of the cost
    """
#     # we will return this state if items in prev_assigned cannot be fitted back 
#     old_state = copy.deepcopy(destroyed)
    
    # randomise the copied task list
    random_state.shuffle(destroyed.unassigned)
            
    # let's first make sure the previous jobs are assigned back as they were without any changes 
    if len(destroyed.prev_assigned) != 0: 
        for job in destroyed.prev_assigned:
            
            possible_slots = destroyed.get_possible_slots(job[0])
            if len(possible_slots) > 1:
                pickup_idx = random_state.randint(len(possible_slots) - 1)
                delivery_idx = random_state.randint(pickup_idx + 1, len(possible_slots))
                # try to assign the job
                result = destroyed.can_assign(job[0], possible_slots[pickup_idx], possible_slots[delivery_idx])
                # assign if possible
                if result:
                    destroyed.assign_job(job[0], possible_slots[pickup_idx], possible_slots[delivery_idx])
                    destroyed.prev_assigned.remove(job)
                else: 
                    destroyed.assign_job(job[0], job[1], job[2])
                    destroyed.prev_assigned.remove(job)
                
    if len(destroyed.prev_assigned) != 0:
        print('error')
    
    ### if the prev_assigned is not empty, simply just return destroy, the new solution state will not be accepted. 
    
    for job in destroyed.unassigned:
        possible_slots = destroyed.get_possible_slots(job)
        
        # sort the slots 
        possible_slots = sorted(possible_slots)
        
        # pick the good start index 
        end_range = 0
        for x in range(len(possible_slots)):
            if possible_slots[x] <= job.pickup_time + 15: 
                end_range = x
            else:
                break 
        
        if len(possible_slots) > 1 and end_range > 1:
                
#             pickup_idx = random_state.randint(len(possible_slots) - 1)
            pickup_idx = random_state.randint(end_range)
            delivery_idx = random_state.randint(pickup_idx + 1, len(possible_slots))
            # try to assign the job
            result = destroyed.can_assign(job, possible_slots[pickup_idx], possible_slots[delivery_idx])
            # assign if possible
            if result:
                print('i assigned', job)
                destroyed.assign_job(job, possible_slots[pickup_idx], possible_slots[delivery_idx])

    return destroyed
