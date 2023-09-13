# from IPython.core.debugger import set_trace

import copy
import numpy.random as random
import time as timer

from Job import Job
from Rider import Rider, EventType
from alns import State
from Variables import FUEL_CONSUMPTION, FUEL_PRICE, PENALTY_RATE, BUFFER, SIMTIME_RATIO, PAY_DIVIDE


class GSP(State):

    def __init__(self, jobs: list[Job], rider: Rider):

        self.all_jobs = jobs  # immutable list of all tasks available

        # for the usage of destroy, repair, can assign
        self.assigned = []  # list containing the job objects assigned
        self.unassigned = jobs
        self.prev_assigned = []  # if filled, alns is running for dynamic jobs
        self.dynamic_jobs = []

        self.rider = rider
        self.shift_started_at = None
        # self.dist_time_matrix = get_travel_time(jobs, rider.shift_start_loc, rider.shift_end_loc)

    def copy(self):
        return copy.deepcopy(self)

    def start_shift(self):
        self.shift_started_at = timer.time_ns() // 1000000  # in milliseconds

    def can_assign(self, job: Job, pickup_time: int, delivery_time: int):
        return self.rider.can_assign(job, pickup_time, delivery_time, self.shift_started_at, dist_time_mat=None)

    def assign_job(self, job, pickup_time, delivery_time):
        if self.can_assign(job, pickup_time, delivery_time):
            # add to rider
            self.rider.schedule[pickup_time] = (EventType.PICKUP, job.id)
            self.rider.schedule[delivery_time] = (EventType.DELIVERY, job.id)
            self.rider.current_jobs[job.id] = job
            self.rider.current_weight += job.weight

            # add to the assigned jobs (for quick tracing of tasks)
            self.assigned.append(job)
            self.unassigned.remove(job)
            # print(f'Job {job.id} assigned to rider for pickup at {pickup_time} and delivery at {delivery_time}')
        else:
            raise Exception(f'Cannot assign job {job.id} to rider.')

    def remove_job(self, job_id):
        if job_id in self.rider.current_jobs:
            job = self.rider.current_jobs[job_id]
            # find job in schedule
            schedule_time = [x[0] for x in self.rider.schedule.items() if x[1][1] == job_id]

            # if shift has started, past jobs cannot be shifted
            if self.shift_started_at is not None:
                current = timer.time_ns() // 1000000
                elapsed = (current - self.shift_started_at) / SIMTIME_RATIO
                if min(schedule_time) < elapsed:
                    return

            # remove from rider
            for time in schedule_time:
                del self.rider.schedule[time]
            del self.rider.current_jobs[job_id]
            self.rider.current_weight -= job.weight

            # add to the assigned jobs (for quick tracing of tasks)
            self.assigned.remove(job)
            self.unassigned.append(job)
            # print(f'Job {job.id} removed from rider')
        else:
            raise Exception(f'Job {job_id} cannot be removed. Was not assigned to rider in first place.')

    def get_possible_slots(self, job):
        filled_slots = set(self.rider.schedule.keys())
        if self.shift_started_at:
            current = timer.time_ns() // 1000000
            elapsed = (current - self.shift_started_at) / SIMTIME_RATIO
            all_slots = set(range(int(elapsed) + BUFFER, self.rider.shift_end_time + 1))
        else:
            all_slots = set(range(self.rider.shift_start_time, self.rider.shift_end_time + 1))
        empty_slots = all_slots.difference(filled_slots)
        return list(filter(lambda t: job.pickup_time <= t, empty_slots))

    def initialise(self, seed=None):  # later upgrade to random
        # init random seed
        if seed is None:
            seed = 606
        random.seed(seed)

        # randomise the unassigned jobs
        random.shuffle(self.unassigned)

        for job in self.unassigned:
            possible_slots = self.get_possible_slots(job)
            
            if len(possible_slots) > 1:
                pickup_idx = random.randint(len(possible_slots) - 1)
#                 pickup_idx = random.randint(start_range - 1)
                delivery_idx = random.randint(pickup_idx + 1, len(possible_slots))
                # try to assign the job
                result = self.can_assign(job, possible_slots[pickup_idx], possible_slots[delivery_idx])
                # assign if possible
                if result:
                    self.assign_job(job, possible_slots[pickup_idx], possible_slots[delivery_idx])
                    
        return self.objective()

    def show_info(self):
        slots = self.rider.schedule.keys()
        slots = sorted(slots)
        print('current time slots:', slots)
        assigned_jobs = [[x.id, x.start, x.end, x.pay, x.weight] for x in self.assigned]
        assigned_jobs = sorted(assigned_jobs, key=lambda x: x[0])
        print('assigned jobs:', assigned_jobs)

    def get_penalty(self):
        def calc_penalty(actual_delivery_time, job):
            if actual_delivery_time <= job.delivery_time:
                return 0
            return PENALTY_RATE * job.pay * PAY_DIVIDE

        # 50% penalty for each late delivery
        penalty = [calc_penalty(i, self.rider.current_jobs[jobId])
                   for i, (event, jobId) in self.rider.schedule.items() if event is EventType.DELIVERY]

        return sum(penalty)

    def get_fuel_cost(self):
        # remove petrol cost for total distance travelled
        fuel_cost = FUEL_CONSUMPTION * self.rider.get_cumulative_distance() * FUEL_PRICE
        return fuel_cost

    def objective(self):
        pay = [x.pay * PAY_DIVIDE for x in self.assigned]

        # negative objective value because alns library is a minimisation function
        return -sum(pay) + self.get_penalty() + self.get_fuel_cost()
