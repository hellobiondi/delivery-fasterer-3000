import pandas as pd
import pickle
import time

from Job import Job
from Variables import EventType, MIN_REST_TIME, MAX_WORK_DURATION, PICKUP_WINDOW, SIMTIME_RATIO

with open('../data/dist_time_mat.pkl', 'rb') as file:
    dist_time_mat, _, _ = pickle.load(file)

missing_dist_mat = set()

def calc_dist(start, start_type, end, end_type):
    try:
        if start_type == EventType.PICKUP:
            start_idx = 2 * start
        else:
            start_idx = 2 * start + 1

        if end_type == EventType.PICKUP:
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

class Rider:
    def __init__(self, shift_start_time: str, shift_end_time: str,
                 shift_start_loc: tuple[float, float], shift_end_loc: tuple[float, float],
                 max_weight: float):
        timezone = '+08:00'
        shift_start_time = int(pd.to_datetime(f"{shift_start_time} {timezone}"
                                              , utc=True).timestamp())
        shift_end_time = int(pd.to_datetime(f"{shift_end_time} {timezone}"
                                            , utc=True).timestamp())

        self.original_start_time = shift_start_time // 60
        self.original_end_time = shift_end_time // 60

        # scaled shift start and end times in minutes
        self.shift_start_time = 0
        self.shift_end_time = (shift_end_time - shift_start_time) // 60

        self.shift_start_loc = shift_start_loc  # tuple of lat, lon
        self.shift_end_loc = shift_end_loc

        self.max_weight = max_weight  # kg

        self.current_weight = 0
        self.schedule = {}  # dictionary key: time, values: (eventtype, job id)
        self.current_jobs = {}

        print(self)

    def can_assign(self, job: Job, pickup_time: int, delivery_time: int, shift_started_at, dist_time_mat):
        this = self

        # checks that proposed pickup and delivery time are within shift hours
        # cannot start at shift start and shift end (assume need to travel from shift start and to shift end locations
        def _check_within_shift_hours(this, _, pickup_time, delivery_time, __):
            return pickup_time > this.shift_start_time and delivery_time < this.shift_end_time

        def _check_viable(_, __, pickup_time, delivery_time, shift_started_at):
            # if shift has started, cannot assign job to past time
            if shift_started_at is not None:
                current = time.time_ns() // 1000000
                elapsed = (current - shift_started_at) / SIMTIME_RATIO
                if pickup_time < elapsed or delivery_time < elapsed:
                    return False
            return True

        # check that actual timings are realistic
        def _check_expected_timings(_, job, pickup_time, delivery_time, __):
            return job.pickup_time <= pickup_time < delivery_time

        def _check_pickup_window(_, job, pickup_time, __, ___):
            return pickup_time - job.pickup_time <= PICKUP_WINDOW

        # checks that the slots are not already occupied by other jobs
        def _check_slot_availability(this, _, pickup_time, delivery_time, __):
            return pickup_time not in self.schedule.keys() and delivery_time not in self.schedule.keys()

        # check that there is a minimum rest period after every max work duration
        # checks that rider's max weight limit is not exceeded at particular time
        def _check_rest_weight_constraint(this, job, pickup_time, delivery_time, _):
            proposed_schedule = this.schedule.copy()
            proposed_schedule[pickup_time] = (EventType.PICKUP, job.id)
            proposed_schedule[delivery_time] = (EventType.DELIVERY, job.id)

            new_jobs = this.current_jobs.copy()
            new_jobs[job.id] = job

            keys = list(proposed_schedule.keys())
            keys.sort()

            prev_time = keys[0]
            break_ended_at = prev_time
            prev_event, prev_job_id = proposed_schedule[prev_time]
            prev_job = new_jobs[prev_job_id]
            if prev_event is EventType.PICKUP:
                current_weight = prev_job.weight
            else:
                raise Exception(f'First job cannot be delivery.')

            break_timings = [prev_time]

            for current_time in keys[1:]:
                current_event, current_job_id = proposed_schedule[current_time]
                current_job = new_jobs[current_job_id]
                if current_event is EventType.PICKUP:
                    current_weight += current_job.weight
                else:
                    current_weight -= current_job.weight

                dist, travel_time = calc_dist(prev_job_id, prev_event, current_job_id, current_event)
                time_diff = current_time - prev_time

                # check if allocated time - travel time is more than required break
                if time_diff - travel_time > MIN_REST_TIME:
                    # see if break should be taken first to avoid exceeding max duration
                    if prev_time - break_ended_at + travel_time <= MAX_WORK_DURATION:
                        # travel to next location first then take break
                        break_ended_at = current_time
                    else:
                        # break first then travel to next location
                        break_ended_at = prev_time + MIN_REST_TIME
                    break_timings.append(break_ended_at)

                cum_work_hours = current_time - break_ended_at

                # check if cumulated work hours exceed max duration allowed without rest
                # check if current weight exceeded max weight carryable
                if cum_work_hours > MAX_WORK_DURATION or current_weight > this.max_weight:
                    return False

                prev_time = current_time
                prev_job_id = current_job_id
                prev_event = current_event

            return True

        # checks the travel time between two sequential locations
        def _check_travel_time_dist(this, job, pickup_time, delivery_time, _, dist_time_mat=None):
            proposed_schedule = this.schedule.copy()
            proposed_schedule[pickup_time] = (EventType.PICKUP, job.id)
            proposed_schedule[delivery_time] = (EventType.DELIVERY, job.id)

            new_jobs = this.current_jobs.copy()
            new_jobs[job.id] = job

            # add job to schedule and check schedule validity
            before_pickup = max(list(filter(lambda t: t < pickup_time, proposed_schedule.keys())), default=-1)
            after_pickup = min(list(filter(lambda t: t > pickup_time, proposed_schedule.keys())), default=delivery_time)

            before_delivery = max(list(filter(lambda t: t < delivery_time, proposed_schedule.keys())),
                                  default=pickup_time)
            after_delivery = min(list(filter(lambda t: t > delivery_time, proposed_schedule.keys())), default=-1)

            # check events before pickup
            if before_pickup > -1:
                event, check_job_Id = proposed_schedule[before_pickup]
                dist, travel_time = calc_dist(check_job_Id, event, job.id, EventType.PICKUP)
                time_diff = pickup_time - before_pickup
            else:
                dist, travel_time = calc_dist(0, EventType.PICKUP, job.id, EventType.PICKUP)
                time_diff = pickup_time
            if travel_time > time_diff:
                return False

            # check events after pickup
            event, check_job_Id = proposed_schedule[after_pickup]
            dist, travel_time = calc_dist(job.id, EventType.PICKUP, check_job_Id, event)
            time_diff = after_pickup - pickup_time
            if travel_time > time_diff:
                return False

            # check events before delivery
            event, check_job_Id = proposed_schedule[before_delivery]
            dist, travel_time = calc_dist(check_job_Id, event, job.id, EventType.DELIVERY)
            time_diff = delivery_time - before_delivery
            if travel_time > time_diff:
                return False

            # check events after delivery
            if after_delivery > -1:
                event, check_job_Id = proposed_schedule[after_delivery]
                dist, travel_time = calc_dist(job.id, EventType.DELIVERY, check_job_Id, event)
                time_diff = after_delivery - delivery_time
                if travel_time > time_diff:
                    return False
            else:
                dist, travel_time = calc_dist(job.id, EventType.DELIVERY, 0, EventType.DELIVERY)
                if delivery_time + travel_time > self.shift_end_time:
                    return False

            return True

        checks = [_check_within_shift_hours,
                  _check_viable,
                  _check_expected_timings,
                  _check_pickup_window,
                  _check_slot_availability,
                  _check_rest_weight_constraint,
                  _check_travel_time_dist]

        for check in checks:
            assignable = check(this, job, pickup_time, delivery_time, shift_started_at)
            if not assignable:
                # print(f'{check.__name__} failed for job {job.id}')
                return False

        return True

    def get_cumulative_distance(self):
        cum_dist = 0

        prev_job_id = 0
        prev_event = EventType.PICKUP

        keys = list(self.schedule.keys())
        keys.sort()

        for key in keys:
            event, jobId = self.schedule[key]
            dist, _ = calc_dist(prev_job_id, prev_event, jobId, event)
            cum_dist += dist

            prev_job_id = jobId
            prev_event = event

        dist, _ = calc_dist(prev_job_id, prev_event, 0, EventType.DELIVERY)
        return cum_dist + dist

    def __repr__(self):
        return f'Rider starting at {self.shift_start_time} at {self.shift_start_loc} ending at {self.shift_end_time} at {self.shift_end_loc}'
