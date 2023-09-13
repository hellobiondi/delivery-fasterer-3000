from Job import Job
from Rider import Rider
import pickle
import pandas as pd
from datetime import date, timedelta
import time


def parse_scheduled(file_loc: str, rider: Rider):
    with open(file_loc, 'rb') as f:
        data = pickle.load(f)

    timezone = '+08:00'

    tmr = date.today() + timedelta(days=1)
    tmr_str = tmr.strftime("%m/%d/%Y") + ' 12:00:00 AM'

    today = time.time() // 60

    job_date = '3/17/2023 12:00:00 AM'

    def translate_time(t, remove_date, add_date):
        remove_date_min = int(pd.to_datetime(f"{remove_date} {timezone}", utc=True).timestamp()) // 60
        add_date_min = int(pd.to_datetime(f"{add_date} {timezone}", utc=True).timestamp()) // 60
        return t - remove_date_min + add_date_min - rider.original_start_time

    data['ExpectedPickupTime'] = data['ExpectedPickupTime'].apply(lambda t: translate_time(t, job_date, tmr_str))
    data['ExpectedDeliveryTime'] = data['ExpectedDeliveryTime'].apply(lambda t: translate_time(t, job_date, tmr_str))
    data['OrderReceivedTime'] = data['OrderReceivedTime'].apply(lambda t: today)

    Jobs = data.apply(lambda row: Job(id=row.name,
                                      order_received_at=row['OrderReceivedTime'],
                                      platform=row['Platform'],
                                      type=row['DeliveryType'],
                                      pickup_loc=row['PickupLocation'],
                                      delivery_loc=row['DeliveryLocation'],
                                      pickup_time=row['ExpectedPickupTime'],
                                      delivery_time=row['ExpectedDeliveryTime'],
                                      weight=row['Weight'],
                                      pay=row['Payout']), axis=1).values.tolist()

    return Jobs


def parse_time(seconds: int, rider: Rider):
    timezone = '+08:00'
    job_date = '3/19/2023 12:00:00 AM'
    tmr = date.today() + timedelta(days=1)
    tmr_str = tmr.strftime("%m/%d/%Y") + ' 12:00:00 AM'

    remove_date_min = int(pd.to_datetime(f"{job_date} {timezone}", utc=True).timestamp()) // 60
    add_date_min = int(pd.to_datetime(f"{tmr_str} {timezone}", utc=True).timestamp()) // 60
    return seconds - remove_date_min + add_date_min - rider.original_start_time
