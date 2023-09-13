'''
To run:

1) cd heuristic
2) python output_checker.py <solution file path> <Jobs.pkl file path>
'''

import re
import argparse
import pickle

from Parser import parse_scheduled
from Rider import Rider
from Job import Job

from Variables import MAX_WEIGHT, START_TIME, END_TIME, START_LOC, END_LOC, PENALTY_RATE, \
    MIN_REST_TIME, MAX_WORK_DURATION, FUEL_CONSUMPTION, FUEL_PRICE, PICKUP_WINDOW, PAY_DIVIDE

parser = argparse.ArgumentParser(description='load data')
parser.add_argument(dest='solution', type=str, help='solution')
parser.add_argument(dest='data', type=str, help='data')
args = parser.parse_args()

# instance file
solution_file = args.solution
job_file = args.data

# parse input data
rider = Rider(shift_start_time=START_TIME,
              shift_end_time=END_TIME,
              shift_start_loc=START_LOC,
              shift_end_loc=END_LOC,
              max_weight=MAX_WEIGHT)

with open('../data/dist_time_mat.pkl', 'rb') as file:
    dist_time_mat, _, _ = pickle.load(file)

missing_dist_mat = set()


def calc_dist(start, start_type, end, end_type):
    try:
        if start_type == 'PICKUP':
            start_idx = 2 * start
        else:
            start_idx = 2 * start + 1

        if end_type == 'PICKUP':
            end_idx = 2 * end
        else:
            end_idx = 2 * end + 1

        dist, duration = dist_time_mat[start_idx, end_idx]
        return dist, duration
    except:
        if (start, end, start_type, end_type) not in missing_dist_mat:
            missing_dist_mat.add((start, end, start_type, end_type))
            with open('../data/missing.pkl', 'wb') as file:
                pickle.dump(missing_dist_mat, file)

        return 0, 0


job_list = parse_scheduled(job_file, rider)
job_dict = {job.id: job for job in job_list}

# load solution
output = open(solution_file, 'r')

line = output.readline()
pattern = r'Objective: -(\d+.\d+), Pay: (\d+.\d+), Penalty: (\d+.\d+), Fuel cost: (\d+.\d+)'
cobjective, cpay, cpenalty, cfuel_cost = re.match(pattern, line.strip()).groups()
cobjective = -1 * float(cobjective)
cpay = float(cpay)
cpenalty = float(cpenalty)
cfuel_cost = float(cfuel_cost)

line = output.readline()
assigned_pattern = r'Assigned: \[(((?:\d+),? ?)*)\]'
assigned, _ = re.match(assigned_pattern, line.strip()).groups()
if len(assigned) > 0:
    assigned = assigned.split(', ')
assigned = [int(a) for a in assigned]

line = output.readline()
rider_pattern = r'Rider starting at (\d+) at \((\d+.\d+), (\d+.\d+)\) ending at (\d+) at \((\d+.\d+), (\d+.\d+)\)'
shift_start, start_lat, start_lon, shift_end, end_lat, end_lon = re.match(rider_pattern, line.strip()).groups()
shift_start, start_lat, start_lon, shift_end, end_lat, end_lon = int(shift_start), float(start_lat), float(
    start_lon), int(shift_end), float(end_lat), float(end_lon)

schedule_pattern = r'(\d+): (\w+) Job: (\d+); Expected .+ at (-?\d+) at loc: \((\d+.\d+), (\d+.\d+)\)'
schedule = {}
penalty = 0
payout = 0
cum_dist = 0
cum_work_hours = 0
last_break = 0

picked_up = set()
delivered = set()

while True:
    line = output.readline()

    if not line:
        keys = list(schedule.keys())
        keys.sort()

        cum_weight = 0
        prev_time = 0
        prev_job = Job(id=0)
        prev_event = 'PICKUP'

        firstJob = True
        for key in keys:
            event, job = schedule[key]

            if firstJob:
                # check first job time is more than shift start time
                if key < shift_start:
                    raise Exception(f'Job {job.id} cannot start earlier than shift start time')

                last_break = key
                firstJob = False

            if event == 'PICKUP':
                # check that job actual pickup time is after job expected pickup time
                if key < job.pickup_time:
                    raise Exception(f'Cannot pick up {job.id} earlier than expected pickup time')

                # check that job actual pickup time is no more than x min from expected pickup time
                if key > job.pickup_time + PICKUP_WINDOW:
                    raise Exception(f'Cannot pick up {job.id} more than {PICKUP_WINDOW} min from expected pickup time')

                cum_weight += job.weight
                picked_up.add(job.id)
            elif event == 'DELIVERY':
                # check that job actual delivery time is after job actual pickup time
                if job.id not in picked_up:
                    raise Exception(f'Cannot deliver {job.id} before picking it up!')

                # add payout to total pay
                payout += job.pay * PAY_DIVIDE
                delivered.add(job.id)

                # if late, add to penalty
                if key > job.delivery_time:
                    penalty += PENALTY_RATE * job.pay * PAY_DIVIDE

                # remove weight from cumulative weight
                cum_weight -= job.weight

            # check that travel time between current and prev loc < time diff
            dist, travel_time = calc_dist(prev_job.id, prev_event, job.id, event)
            time_diff = key - prev_time
            if travel_time > time_diff:
                raise Exception(f'Travel time {travel_time} is more than time diff {time_diff}'
                                f' for jobs {prev_job} and {job.id}')

            # if time diff - travel time > rest duration, update break hours
            if time_diff - travel_time > MIN_REST_TIME:
                cum_work_hours = 0
                if prev_time - last_break + travel_time <= MAX_WORK_DURATION:
                    last_break = key
                else:
                    last_break = prev_time + MIN_REST_TIME
            else:
                cum_work_hours = key - last_break

            # check that cumulative work hours not exceeded
            if cum_work_hours > MAX_WORK_DURATION:
                raise Exception(f'Work hours {cum_work_hours} exceeded without rest at job {job.id}.'
                                f' Last break at {last_break}')

            # check cumulative weight < max weight
            if cum_weight > 100:
                raise Exception(f'Weight exceeded at job {job.id}')

            # add travelled dist to cumulative dist
            cum_dist += dist

            # update current as prev
            prev_time = key
            prev_job = job
            prev_event = event

        # check travel time to end location < shift end time
        dist, travel_time = calc_dist(prev_job.id, prev_event, 0, 'DELIVERY')
        cum_dist += dist
        if prev_time + travel_time > shift_end:
            raise Exception(f'End time cannot be later than shift end time')

        # check jobs in schedule match assigned list
        for j in delivered:
            if j not in assigned:
                raise Exception(f'Job {j} delivered but not in assigned list')

        # check jobs in pickup and delivered match each other
        for j in picked_up:
            if j not in delivered:
                raise Exception(f'Job {j} picked up but not in delivered list')

        # check objective value
        fuel_cost = FUEL_CONSUMPTION * cum_dist * FUEL_PRICE
        calc_objective = - payout + penalty + fuel_cost

        if round(calc_objective, 2) != round(cobjective, 2):
            raise Exception(f'Actual objective {calc_objective: 2f} different from gsp objective {cobjective: 2f}\n'
                            f'Actual pay {payout: 2f}, gsp pay {cpay: 2f}\n'
                            f'Actual penalty {penalty: 2f}, gsp penalty {cpenalty: 2f}\n'
                            f'Actual fuel cost {fuel_cost: 2f}, gsp fuel cost {cfuel_cost: 2f}')

        print("Check complete. Solution viable.")

        break
    else:
        time, event, jobId, _, __, ___ = re.match(schedule_pattern, line.strip()).groups()
        time, jobId = int(time), int(jobId)
        schedule[time] = (event, job_dict[jobId])

output.close()
