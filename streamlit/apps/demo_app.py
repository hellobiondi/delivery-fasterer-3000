import streamlit as st
import pandas as pd
import pickle
from streamlit_folium import folium_static
import subprocess
import sys
import shutil
import time
import multiprocessing

from components import maps
import os

def get_map_data(df, type):
    df = df[[f'{type}Lat', f'{type}Long']]
    map_data = df.values.tolist()
    return map_data

def run_alns():
    subprocess.run([f"{sys.executable}", "../heuristic/alns_main.py"])

def send_stream():
    subprocess.run([f"{sys.executable}", "../heuristic/streaming/bin/sendStream.py", "../heuristic/streaming/Jobs_dynamic.csv", "order-stream"])

def app():
    # HTML Description
    demo = '''
        <h2>Demo of our ALNS model</h2>
    '''
    st.markdown(demo, unsafe_allow_html=True)

    with open("./data/Jobs.pkl", 'rb') as f:
        df = pickle.load(f)

    display_df = pd.read_csv("./assets/Viz_Jobs.csv")

    st.markdown("<h3>Dataframe of input data</h3>", unsafe_allow_html=True)
    st.dataframe(display_df)

    df[['pickupLat', 'pickupLong']] = pd.DataFrame(df['PickupLocation'].tolist(), index=df.index)
    df[['deliveryLat', 'deliveryLong']] = pd.DataFrame(df['DeliveryLocation'].tolist(), index=df.index)
    pickup_map_data = get_map_data(df, 'pickup')
    delivery_map_data = get_map_data(df, 'delivery')
    pickupFig = maps.get_map(pickup_map_data)
    deliveryFig = maps.get_map(delivery_map_data)

    st.markdown("<h3>Map of pickup locations</h3>", unsafe_allow_html=True)
    folium_static(pickupFig)

    st.markdown("<h3>Map of delivery locations</h3>", unsafe_allow_html=True)
    folium_static(deliveryFig)

    # button to run ALNS
    generate_schedule_button = st.button("Generate schedule using ALNS!")

    if generate_schedule_button:
        generate_schedule_alert = """
        <p>
                Note: the model may take some time to go through all iterations. <i><b>Clicking on the button again or to another page 
                on the navigation pane will interrupt the hill climbing process</b></i>.
            </p>
        """
        st.markdown(generate_schedule_alert, unsafe_allow_html = True)

        progress_text = "Hillclimbing in progress, please wait."
        # progress_bar = st.progress(0, text=progress_text)

        a = multiprocessing.Process(target=run_alns, name="ALNS")
        s = multiprocessing.Process(target=send_stream, name="stream")
        a.start()

        progress_bar = st.progress(0, text=progress_text)
        for percent_complete in range(100):
            time.sleep(0.9) # hardcoded progress bar..
            progress_bar.progress(percent_complete + 1, text=progress_text)

        st.info("Streaming of dynamic jobs has started")
        s.start()
