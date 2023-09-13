#!/usr/bin/env python

"""Generates a stream to Kafka from a time series csv file.
"""

import argparse
import csv
import json
import sys
import time
from dateutil.parser import parse
from confluent_kafka import Producer
import socket


def acked(err, msg):
    if err is not None:
        print("Failed to deliver message: %s: %s" % (str(msg.value()), str(err)))
    else:
        print("Message produced: %s" % (str(msg.value())))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('filename', type=str,
                        help='Time series csv file.')
    parser.add_argument('topic', type=str,
                        help='Name of the Kafka topic to stream.')
    parser.add_argument('--speed', type=float, default=1, required=False,
                        help='Speed up time series by a given multiplicative factor.')
    args = parser.parse_args()

    topic = args.topic
    p_key = args.filename

    conf = {'bootstrap.servers': "localhost:9092",
            'client.id': socket.gethostname()}
    producer = Producer(conf)

    rdr = csv.reader(open(args.filename, encoding='utf-8-sig'))

    firstline = True

    # columns_list = ['Order Time', 'Pickup Lat', 'Pickup Lon', 'Expected Pickup Time', 'Delivery Lat', 'Delivery Lon',
    # 'Distance (KM)', 'Weight', 'Payout', 'Travel Type', 'Buffer time (min)', 'Expected Pickup DateTime (UTC)',
    # 'Expected Pickup DateTime (sec)', 'Travel Distance (m)', 'Minimum Gap between Pickup and Delivery time (sec)',
    # 'Delivery Duration (sec)', 'Expected Delivery Time (GMT+8)', 'Expected pickup time GMT+8 (5 min blocks)', 'Expected delivery time GMT+8 (5 min blocks)']
    
    columns_list = []

    header_line = next(rdr, None)
    # print(header_line)

    columns_list = [col for col in header_line]

    # next(rdr)

    while True:

        try:

            if firstline is True:
                line1 = next(rdr, None)
                result = {}
                firstTimestamp = line1[0]

                for i in range(len(columns_list)):
                    result[columns_list[i]] = line1[i]

                # Convert dict to json as message format
                jresult = json.dumps(result)
                firstline = False

                producer.produce(topic, key=p_key, value=jresult, callback=acked)

            else:
                line = next(rdr, None)
                d1 = parse(firstTimestamp)
                d2 = parse(line[0])
                diff = ((d2 - d1).total_seconds())/args.speed
                time.sleep(diff)

                result = {}

                for i in range(len(columns_list)):
                    result[columns_list[i]] = line[i]

                jresult = json.dumps(result)

                producer.produce(topic, key=p_key, value=jresult, callback=acked)

            producer.flush()

        except TypeError:
            sys.exit()


if __name__ == "__main__":
    main()
