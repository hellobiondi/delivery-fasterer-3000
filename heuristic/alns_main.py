import numpy.random as rnd
import matplotlib.pyplot as plt
import os
import copy
import time
import sched
from collections import deque

import time as timer 
import random 
random.seed(123)

from Rider import Rider
from Job import Job
from Parser import parse_scheduled, parse_time
from GSP import GSP
from alns import ALNS
from operators import random_destroy, random_destroy_multi, random_destroy_lowest_pay, random_repair, random_repair_on_time, random_repair_best_pay, repair_long 
from operators import dynamic_random_destroy, dynamic_random_repair
from Variables import TOPIC_NAME, INITIAL_ITERATIONS, DYNAMIC_ITERATIONS, CRITERION, WEIGHTS, LAMBDA, MAX_WEIGHT,\
    START_TIME, END_TIME, START_LOC, END_LOC, EventType, SIMTIME_RATIO

import sys
import socket
import json
from confluent_kafka import Consumer, KafkaError, KafkaException

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import pickle

max_static_job = 2757  # dynamic job id counter
gsp: GSP = None
dynamic_jobs = deque()
kafka_event = None

rider = Rider(shift_start_time=START_TIME,
              shift_end_time=END_TIME,
              shift_start_loc=START_LOC,
              shift_end_loc=END_LOC,
              max_weight=MAX_WEIGHT)


def save_output(gsp: GSP, type: str):
    str_builder = [f'Objective: {gsp.objective()}, Pay: {-1 * gsp.objective() + gsp.get_fuel_cost() + gsp.get_penalty()}, '
                   f'Penalty: {gsp.get_penalty()}, Fuel cost: {gsp.get_fuel_cost()}']
    str_builder += [f'Assigned: {[job.id for job in gsp.assigned]}']
    str_builder += [f'Number of assigned jobs: {len(gsp.assigned)}']
    str_builder += [str(gsp.rider)]
    sorted_keys = list(gsp.rider.schedule.keys())
    sorted_keys.sort()
    for key in sorted_keys:
        event = gsp.rider.schedule[key][0]
        job_id = gsp.rider.schedule[key][1]
        job = next(filter(lambda x: x.id == job_id, gsp.assigned))
        if event == EventType.PICKUP:
            str_builder += [f'{key}: PICKUP Job: {job_id}; Expected pickup at {job.pickup_time} at loc: {job.pickup_loc}']
        else:
            str_builder += [f'{key}: DELIVERY Job: {job_id}; Expected delivery at {job.delivery_time} at loc: {job.delivery_loc}']
    isExist = os.path.exists('./output/')
    if not isExist:
        # Create a new directory because it does not exist
        os.makedirs('./output/')
    with open(f'./output/{type}_output.txt', 'w') as f:
        f.write('\n'.join(str_builder))


def header_process(msg):  # for processing of headers
    val = msg.value()
    dval = json.loads(val)
    line = [item[0] for item in dval.items()]
    return line


def msg_process(msg):  # processing of regular message
    val = msg.value()
    dval = json.loads(val)
    received_time = int(time.time() // 60)
    expected_pickup = parse_time(int(dval['ExpectedPickupTime']), rider)
    expected_delivery = parse_time(int(dval['ExpectedDeliveryTime']), rider)
    new_job = Job(id=max_static_job + int(dval['JobId']),
                  order_received_at=received_time,
                  platform=dval['Platform'],
                  type=dval['DeliveryType'],
                  pickup_loc=tuple(map(float, dval['PickupLocation'][1:-1].split(', '))),
                  delivery_loc=tuple(map(float, dval['DeliveryLocation'][1:-1].split(', '))),
                  pickup_time=expected_pickup,
                  delivery_time=expected_delivery,
                  weight=float(dval['Weight']),
                  pay=float(dval['Payout']))
    return new_job

def save_gantt(solution, i):
    sorted_jobs = solution.assigned
    sorted_jobs = sorted(sorted_jobs, key=lambda x: x.pickup_time)

    final_dict = {'job':[],
                'start':[],
                'end':[],
                'width':[]}


    for job in sorted_jobs: 
        final_dict['job'].append(str(job.id))
        final_dict['start'].append(job.pickup_time)
        final_dict['end'].append(job.delivery_time)
        final_dict['width'].append(job.delivery_time - job.pickup_time+1)

        
    df = pd.DataFrame(final_dict)
    chart = plt.figure(figsize=(12,8))
    plt.barh(y=df['job'], width=df['width'], left=df['start'])
    plt.xlabel("slot / min")
    plt.xticks(range(0, max(df.end), 60))
    plt.ylabel("Job ID")
    plt.title(f"Worker Gantt Chart, Iteration {i}")
    plt.grid()
    plt.savefig(f'output/gantt_{i}.png', bbox_inches='tight')
    # plt.show()

def save_objective(objective, i):
    with open(f'output/objective_{i}.pkl', 'wb') as f:
        pickle.dump(objective, f)
        f.close()
        
def cancel_event(scheduler, alns: ALNS, iter: int):
    global dynamic_jobs, gsp
    
    remove = {2: 6,
             }
    
    # get the elasped time: 
    now = timer.time_ns() // 1000000
    elapsed = (now - gsp.shift_started_at) / SIMTIME_RATIO
    
    select = [] 
    for job in gsp.assigned: 
        schedule_time = [x[0] for x in gsp.rider.schedule.items() if x[1][1] == job.id]
        if schedule_time[0] > elapsed: 
            select.append(job.id)
    print('scan jobs done', len(select), 'found')

    # ensure that there are still jobs that can be removed 
    if len(select) > 3: 
#             # simulate a chance 
#             chance = random.randint(1, 100)
#             print('chance:', chance)
#             if chance < 40:
#                 # choose number of jobs to remove 
#                 to_remove = random.randint(1, 2)
#                 print('jobs canceled:', to_remove)
#                 # select x worker's idx for destruction 
        to_remove = remove[iter]
        random_sample = random.sample(select, to_remove)
        print('something happened, jobs lost:', random_sample)
        for job_id in random_sample: 
            # remove from rider
            gsp.remove_job(job_id)

    # need to clear the list to make sure these job are permanently lost 
    gsp.unassigned = []

    print('new objective value is:', gsp.objective())       


def run_alns(scheduler, alns: ALNS, iter: int):

    if iter <= 32:
        # schedule the next call first
        print('round:', iter)
        scheduler.enter(60, 1, run_alns, (scheduler, alns, iter + 1))
    else:
        shut_down(scheduler)

    # run alns again
    global dynamic_jobs, gsp

    # copy over all dynamic jobs in queue so far
    job_copy = []
    current_length = len(dynamic_jobs)
    for _ in range(current_length):
        job_copy.append(dynamic_jobs.popleft())
    print('going to run alns with ', len(job_copy))

    gsp.dynamic_jobs = job_copy
    if iter == 1:
        gsp.start_shift()

    ## clear out the unassigned from previous ALNS run, we do not require this for dynamic
    gsp.unassigned = []  
    ## we will now repurpose this to hold the dynamic job 
    gsp.unassigned = copy.deepcopy(gsp.dynamic_jobs)
    print(len(gsp.unassigned), 'New Jobs')
    
    ## for each new ALNS call for dynamic, I will re_init the ALNS with new destory and repair function
    random_state = rnd.RandomState(123)
    new_alns = ALNS(random_state)
    new_alns.add_destroy_operator(dynamic_random_destroy)
    new_alns.add_repair_operator(dynamic_random_repair)
        
    result = new_alns.iterate(gsp, WEIGHTS, LAMBDA, CRITERION, iterations=DYNAMIC_ITERATIONS, collect_stats=True)
    solution = result.best_state
    objective = solution.objective()
    print(f'Best objective value: {objective}')
    save_gantt(solution, iter)
    save_objective(objective, iter)
    save_output(solution, f'iter{iter}')

    gsp = solution
#     gsp.prev_assigned = gsp.assigned.copy()
    # I will need this to be empty for a new set, 
    # for each existing job I remove, I will add to prev_assign in destroy function instead 
    gsp.prev_assigned = []
    gsp.dynamic_jobs = []
    
#     if iter == 2:
#         # schedule the event
#         scheduler.enter(3, 1, cancel_event, (scheduler, alns, iter))


def process_stream(scheduler, consumer):
    global kafka_event
    # schedule the next call first
    kafka_event = scheduler.enter(1, 1, process_stream, (scheduler, consumer,))

    # get message and add to dynamic jobs
    global dynamic_jobs

    msg = consumer.poll(0)
    if msg is None:
        return

    if msg.error():
        if msg.error().code() == KafkaError._PARTITION_EOF:
            # End of partition event
            sys.stderr.write('%% %s [%d] reached end at offset %d\n' %
                             (msg.topic(), msg.partition(), msg.offset()))
        elif msg.error().code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
            sys.stderr.write('Topic unknown, creating %s topic\n' %
                             TOPIC_NAME)
        elif msg.error():
            raise KafkaException(msg.error())
    else:
        order = msg_process(msg)
        dynamic_jobs.append(order)
        print('number of dynamic jobs waiting: ', len(dynamic_jobs))


def shut_down(scheduler):
    global kafka_event
    consumer.close()
    scheduler.cancel(kafka_event)
    sys.exit(0)

if __name__ == '__main__':
    jobs = parse_scheduled('../data/Jobs.pkl', rider)
    gsp = GSP(jobs, rider)
    initial_objective = gsp.initialise(1996)
    print(f'Initial objective value: {initial_objective}')
    save_output(gsp, 'initial')

    # ALNS
    random_state = rnd.RandomState(123)
    alns = ALNS(random_state)

    # add destroy
    destroy_operators = [random_destroy,
                        random_destroy_multi,
                        random_destroy_lowest_pay]
    for op in destroy_operators:
        alns.add_destroy_operator(op)

    # add repair
    repair_operators = [random_repair,
                       random_repair_on_time,
                       random_repair_best_pay,
                       repair_long]
    for op in repair_operators:
        alns.add_repair_operator(op)

    result = alns.iterate(gsp, WEIGHTS, LAMBDA, CRITERION, iterations=INITIAL_ITERATIONS, collect_stats=True)
    solution = result.best_state
    objective = solution.objective()
    print(f'Best objective value: {objective}')
    save_output(solution, 'final')

    # plotting the operator statistics 
    figure = plt.figure("operator_counts", figsize=(14, 6))
    figure.subplots_adjust(bottom=0.15, hspace=.5)
    result.plot_operator_counts(figure=figure, title="Operator diagnostics", legend=["Best", "Better", "Accepted"])
    plt.savefig("operator_diagnostic.jpg")
    
    # plotting the search progress 
    _, ax = plt.subplots(figsize=(12, 6))
    result.plot_objectives(ax=ax, lw=2)
    plt.savefig("search_progress.jpg")

    gsp = solution
    ## we will repurpose gsp.prev_assigned, hence the below command is disabled 
    # gsp.prev_assigned = gsp.assigned.copy()

    save_gantt(solution, 0)

    #pass into streamlit since streamlit cannot access alns_main.py even through imports
    objective_tup = (initial_objective, objective)
    with open('output/objective_tup.pkl', 'wb') as f:
        pickle.dump(objective_tup, f)
        f.close()

    conf = {'bootstrap.servers': 'localhost:9092',
            'default.topic.config': {'auto.offset.reset': 'smallest'},
            'group.id': socket.gethostname()}

    consumer = Consumer(conf)
    consumer.subscribe([TOPIC_NAME])

    scheduler = sched.scheduler(time.time, time.sleep)
    # start scheduler to run alns every 60 seconds
    scheduler.enter(60, 1, run_alns, (scheduler, alns, 1))
    # add kafka consumer
    kafka_event = scheduler.enter(1, 1, process_stream, (scheduler, consumer,))
    scheduler.run()

