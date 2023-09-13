from enum import Enum
from alns.criteria import HillClimbing
from datetime import date, timedelta

tmr = date.today() + timedelta(days=1)
date_string = tmr.strftime("%m/%d/%Y")

START_TIME = f'{date_string} 10:00:00 AM'
END_TIME = f'{date_string} 6:00:00 PM'
START_LOC = (1.3323, 103.8474)
END_LOC = (1.2989, 103.8455)

MAX_WEIGHT = 100  # kg
SPEED = 0.833  # km/min

# mandatory 15min rest every 2 hours of consecutive work
MIN_REST_TIME = 15
MAX_WORK_DURATION = 120

PICKUP_WINDOW = 15  # pickup must be no later than 15min from expected

BUFFER = 5  # when shift started, schedule dynamic jobs at least 5min later

# objective value related
FUEL_CONSUMPTION = 0.075  # 7.5 litres per 100km
FUEL_PRICE = 2.75  # sgd per litre
PENALTY_RATE = 0.5
PAY_DIVIDE = 1

TOPIC_NAME = 'order-stream'  # producer stream
SIMTIME_RATIO = 4000  # 1 min of schedule time is 250 ms of runtime
INITIAL_ITERATIONS = 300
DYNAMIC_ITERATIONS = 400
CRITERION = HillClimbing()  # alns acceptance criterion
WEIGHTS = [24, 6, 2, 1]
LAMBDA = 0.96


class EventType(Enum):
    PICKUP = 1
    DELIVERY = 2
