from typing import Union

class Job():
    def __init__(self, id: Union[int,str], order_received_at: int=0, platform: str='', type: str='parcel',
                 pickup_loc: tuple[float, float]=(0,0), delivery_loc: tuple[float, float]=(0,0),
                 pickup_time: int=0, delivery_time: int=0, weight: float=0, pay: float=0):
        self.id = id
        self.order_received_at = order_received_at
        self.platform = platform
        self.type = type
        self.pickup_loc = pickup_loc
        self.delivery_loc = delivery_loc
        self.pickup_time = pickup_time
        self.delivery_time = delivery_time
        self.weight = weight
        self.pay = pay

    def __repr__(self):
        return f'Job Id: {self.id} received at {self.order_received_at}\n \
              Platform: {self.platform}\n \
              Pickup from {self.pickup_loc} after {self.pickup_time}\n \
              Deliver to {self.delivery_loc} before {self.delivery_time}\n \
              Weight: {self.weight}\n \
              Payout: {self.pay}'
