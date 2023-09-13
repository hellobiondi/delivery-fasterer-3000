from datetime import datetime, date, timedelta
import glob
import math
import numpy as np
import os
import pandas as pd
import pickle
import plotly.express as px
import plotly.graph_objects as go
import re
import streamlit as st
import streamlit.components.v1 as components
import subprocess
import sys

@st.cache_data
def generate_addresses():
    # Load addresses
    addresses = pd.read_csv('assets/addresses.csv')
    addresses.drop(columns = ['Type'], inplace = True)

    # Round down to 3 dp to approximate address
    addresses['Lat_round'] = addresses['Lat'].round(3)
    addresses['Lon_round'] = addresses['Lon'].round(3)

    # drop columns and duplicates
    addresses.drop(columns=['Lat','Lon'], inplace = True)
    addresses.drop_duplicates(subset=['Lat_round','Lon_round'], keep='first', inplace=True)

    return addresses

# Function to create LONG dataframe (for map)
@st.cache_data
def create_df_long(filename,rider_start_dt, addresses):
    # create a list containing the strings
    job_info = []

    with open(filename) as file:
        for item in file:
            job_info.append(item)

    # Get start and end times
    start_stop = job_info[2]

    match = re.search(r'starting at (\d+) at \(([\d\.]+),\s([\d\.]+)\) ending at (\d+) at \(([\d\.]+),\s([\d\.]+)\)', start_stop)

    if match:
        start_time = match.group(1)
        start_lat = match.group(2)
        start_lon = match.group(3)
        end_time = match.group(4)
        end_lat = match.group(5)
        end_lon = match.group(6)


    # For the rest of the jobs,
    job_info = job_info[3:]


    # create a DataFrame from the list
    df_long = pd.DataFrame(job_info, columns=['string'])

    # split the string into columns and keep those needed
    df_long[["Actual time","Type","3","Job","5","6","7","Expected time","9","10","Lat","Lon"]] = df_long['string'].str.split(' ', expand=True)
    df_long = df_long[["Actual time","Type","Job","Expected time","Lat","Lon"]]

    df_long['Actual time'] = df_long['Actual time'].str.extract('(\d+)').astype(int)
    df_long['Job'] = df_long['Job'].str.extract('(\d+)').astype(int)
    df_long['Lat'] = df_long['Lat'].str.extract('(\d+\.\d+)')
    df_long['Lon'] = df_long['Lon'].str.extract('(\d+\.\d+)')


    # Add the start and end points
    # start = pd.DataFrame([[start_time, 'START', 0, start_time, start_lat, start_lon]], columns = df_long.columns)
    # end = pd.DataFrame([[end_time, 'END', 10000, end_time, end_lat, end_lon]], columns = df_long.columns)
    # df_long = pd.concat([start,df_long])
    # df_long = pd.concat([df_long,end])
    # df_long.reset_index(inplace = True, drop = True)

    # Convert epoch mins to time
    df_long['Actual time'] = df_long['Actual time'].apply(lambda x: rider_start_dt + timedelta(minutes = int(x)))
    df_long['Expected time'] = df_long['Expected time'].apply(lambda x: rider_start_dt + timedelta(minutes = int(x)))

    # Convert Lat and Lon to float
    df_long['Lat'] = df_long['Lat'].astype(float)
    df_long['Lon'] = df_long['Lon'].astype(float)

    # Create (job) order column
    df_long['Order'] = df_long.index

    # Create empty IsNewJob column to flag new jobs later
    df_long["IsNewJob"] = "First assignment"
    df_long['Size'] = 1

    # Lookup address
    # First we round down to 3 dp to approximate address
    df_long['Lat_round'] = df_long['Lat'].round(3)
    df_long['Lon_round'] = df_long['Lon'].round(3)
    
    df_long = df_long.merge(addresses, on=['Lat_round','Lon_round'], how = 'left').drop_duplicates()
    
    return df_long

# Function to create WIDE dataframe (for gantt)
@st.cache_data
def create_df_wide(df_long):
    df_wide = df_long.set_index('Job')
    df_wide_pickup = df_wide[df_wide['Type']=="PICKUP"].drop(columns=['Type','Order'])
    df_wide_pickup = df_wide_pickup.rename(columns = {'Actual time': 'Pickup actual time',
                                            'Expected time': 'Pickup expected time',
                                            'Lat':'Pickup Lat',
                                            'Lon':'Pickup Lon',
                                            'Address':'Pickup Address'
                                            })
    df_wide_delivery = df_wide[df_wide['Type']=="DELIVERY"].drop(columns=['Type','Order'])
    df_wide_delivery = df_wide_delivery.rename(columns = {'Actual time': 'Delivery actual time',
                                            'Expected time': 'Delivery expected time',
                                            'Lat':'Delivery Lat',
                                            'Lon':'Delivery Lon',
                                            'Address': 'Delivery Address'
                                            })

    df_wide = pd.merge(df_wide_pickup, df_wide_delivery, left_index=True, right_index=True)
    df_wide['Job'] = df_wide.index

    # Create empty IsNewJob column to flag new jobs later
    df_wide["IsNewJob"] = "First assignment"

    # Create (job) order column
    df_wide["Order"] = np.arange(len(df_wide))+1

    return df_wide

# Plot gantt
@st.cache_data
def plot_gantt(data):
    fig = px.timeline(data, x_start="Pickup expected time", x_end="Delivery expected time", y = "Order",
                    hover_data = ["Job"],
                    color = "IsNewJob",
                    width=700, height=500,
                    template = "plotly_white",
                    )

    # Set axis ticks
    fig.update_yaxes(dtick=1, showgrid=True, autorange="reversed")
    fig.update_xaxes(ticklabelmode="period")
    fig.update_layout(title="Shift Schedule", xaxis_title="Day/Time", yaxis_title="Job Order")

    return fig

# Plot line map
@st.cache_data
def plot_line_map(data):
    fig = px.scatter_mapbox(data, lat="Lat", lon="Lon",
                            hover_data = ['Order',"Job",'Expected time','Address'],
                            zoom=3,
                            width=700, height=500,
                            #text="Job",
                            title = "Route",
                            color = 'Type',
                            animation_frame='Order',
                            )
    fig.update_traces(marker={'size': 10})
    fig.update_layout(mapbox_style="carto-positron", mapbox_zoom=10, mapbox_center_lat = 1.35,
        margin={"r":0,"t":0,"l":0,"b":0}, legend={'yanchor':"top", 'y':0.99, 'xanchor':"left", 'x':0.01})
                    
    fig2 = px.line_mapbox(data, lat="Lat", lon="Lon",
                          hover_data = ['Order',"Job",'Expected time','Address'],
                          zoom=3,
                          width=700, height=500,
                          #text="Job",
                          # title = "Route"
                          )
    fig2.update_traces(line_width=1, line_color = 'grey', selector=dict(type='scattermapbox'))


    fig.add_trace(fig2.data[0])
    fig2.layout.update()
    
    return fig

# Plot all points as dots
@st.cache_data
def plot_dot_map(data):
    fig = px.scatter_mapbox(data, lat="Lat", lon="Lon",
                            hover_data = ['Order',"Job",'Expected time','Address'],
                            zoom=3,
                            width=700, height=700,
                            #text="Job",
                            title = "Route",
                            color = 'IsNewJob',
                            #size = 'Size'
                            )
    fig.update_layout(mapbox_style="carto-positron", mapbox_zoom=10, mapbox_center_lat = 1.35,
        margin={"r":0,"t":0,"l":0,"b":0}, legend={'yanchor':"top", 'y':0.99, 'xanchor':"left", 'x':0.01})
                 
    return fig

# Define function to generate a sequential table
@st.cache_data
def plot_seq_table(data):
    seq_table = data[["Order","Job","Expected time", "Type", "Address", "IsNewJob"]].copy()
    seq_table['Time'] = seq_table["Expected time"].dt.time

    # Plot the table
    fig = go.Figure(data=[go.Table(
        columnwidth = [30,30,50,50,100, 50],
        header=dict(values=list(seq_table[["Order","Job","Time", "Type","Address", "IsNewJob"]]),
                    #fill_color='paleturquoise',
                    align='left'),
        cells=dict(values=[seq_table['Order'],seq_table['Job'], seq_table['Time'],seq_table['Type'],seq_table['Address'],seq_table['IsNewJob']],
                #fill_color='lavender',
                align='left'))
    ])

    fig.update_layout(width=600, height=700, margin={"r":0,"t":0,"l":0,"b":0})
    
    return fig

def show_output(txt_path):
    if os.path.isfile(txt_path):
            initial_output = open(txt_path, 'r')
            lines = initial_output.readlines()
            count = 0

            for line in lines:
                count += 1
                st.write("Line{}: {}".format(count, line.strip()))

def show_objective(objective_path, first):
    if first:
        with open(objective_path, 'rb') as f:
            objective_tup = pickle.load(f)
        st.write(f"Initial objective value: {objective_tup[0]}")
        st.write(f"Final objective value: {objective_tup[1]}")

    else:
        with open(objective_path, 'rb') as f:
            objective = pickle.load(f)
        st.write(f"Objective value after next dynamic iteration: {objective}")

def app():
    # HTML Description
    results = '''
        <h2>Results of our ALNS model</h2>
    '''
    st.markdown(results, unsafe_allow_html=True)

    reset_cache = st.button("Click here to reset all results")

    if reset_cache:
        for f in glob.glob("output/gantt*.png"):
            os.remove(f)
        for f in glob.glob("output/objective*.pkl"):
            os.remove(f)
        for f in glob.glob("output/*.txt"):
            os.remove(f)

    addresses = generate_addresses()

    ########## Generate 1st ALNS solution #############

    # Specify the rider start date time
    tmr = date.today() + timedelta(days=1)
    date_string = tmr.strftime("%m/%d/%Y")

    START_TIME = f'{date_string} 10:00:00 AM'   ### INPUT or refer to gsp.rider.shift_start_time
    date_format = '%m/%d/%Y %I:%M:%S %p'
    date_obj = datetime.strptime(START_TIME, date_format)

    # Create the dataframes
    filename = "output/final_output.txt"             ### INPUT file name
    if os.path.isfile(filename):
        rider_start_dt = date_obj
        df_long = create_df_long(filename, rider_start_dt, addresses)
        df_wide = create_df_wide(df_long)

        gantt_plot = plot_gantt(df_wide)
        line_map = plot_line_map(df_long)
        seq_table = plot_seq_table(df_long)

        first_iteration = '''
            <h3>First iteration of ALNS</h3>
        '''
        st.markdown(first_iteration, unsafe_allow_html=True)

        #show objective from first ALNS run
        if os.path.isfile("output/objective_tup.pkl"):
            with open("output/objective_tup.pkl", 'rb') as f:
                objective_tup = pickle.load(f)
            # st.write(f"Initial objective value: {objective_tup[0]}")
            st.write(f"Earnings: ${-round(objective_tup[1], 2)}")

        st.markdown("<h4>Sequence of delivery</h4>", unsafe_allow_html=True)
        st.plotly_chart(seq_table)
        st.markdown("<h4>Map-guided Sequence of delivery</h4>", unsafe_allow_html=True)
        st.plotly_chart(line_map)
        st.markdown("<h4>Gantt chart</h4>", unsafe_allow_html=True)
        st.plotly_chart(gantt_plot)

    ########## Generate dynamic iterations #############

    # Create the dataframes

    i = 1
    while os.path.isfile(f"output/iter{i}_output.txt"):
        filename = f"output/iter{i}_output.txt"
        objectivefilename = f"output/objective_{i}.pkl"
        i += 1

    if os.path.isfile(filename):
        rider_start_dt = date_obj
        df_long2 = create_df_long(filename, rider_start_dt, addresses)
        df_wide2 = create_df_wide(df_long2)

        # Get list of existing jobs
        existing_jobs = df_wide.index

        # Compare with existing solution and indicate new jobs
        df_long2["IsNewJob"] = df_long2["Job"].apply(lambda x: "New" if x not in existing_jobs else "Existing")
        df_wide2["IsNewJob"] = df_wide2["Job"].apply(lambda x: "New" if x not in existing_jobs else "Existing")
        #df_long2['Size'] = df_long2['IsNewJob'].apply(lambda x: 5 if x =="New" else 1)

        dyn_gantt_plot = plot_gantt(df_wide2)
        dyn_dot_map = plot_dot_map(df_long2)
        dyn_seq_table = plot_seq_table(df_long2)
        dyn_line_map = plot_line_map(df_long2)

        dynamic_iteration = f'''
            <h3>Dynamic iterations of ALNS (Iteration {i})</h3>
        '''
        st.markdown(dynamic_iteration, unsafe_allow_html=True)

        if os.path.isfile(objectivefilename):
            with open(objectivefilename, 'rb') as f:
                dyn_objective = pickle.load(f)
            st.write(f"Iteration {i} Earnings: ${-round(dyn_objective, 2)}")

        st.markdown("<h4>Sequence of delivery</h4>", unsafe_allow_html=True)
        st.plotly_chart(dyn_seq_table)
        st.markdown("<h4>Map-guided Sequence of delivery</h4>", unsafe_allow_html=True)
        st.plotly_chart(dyn_line_map)
        st.markdown("<h4>Gantt chart</h4>", unsafe_allow_html=True)
        st.plotly_chart(dyn_gantt_plot)
        # st.plotly_chart(dyn_dot_map)

    # imageCarouselComponent = components.declare_component("image-carousel-component", path="frontend/public")

    # image_urls = []

    # i = 1
    # while os.path.isfile(f"../../output/gantt_{i}.png"):
    #     image_urls.append(f"../../output/gantt_{i}.png")
    #     i += 1

    # selectedImageUrl = imageCarouselComponent(imageUrls=image_urls, height=200)

    # if selectedImageUrl is not None:
    #     st.image(selectedImageUrl)