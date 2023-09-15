# Delivery Fasterer 3000
A metaheuristic-backed project to assist parcel delivery operators in planning a near-optimal schedule that maximises their income given input constraints.

## Motivation behind this project
- Demand for delivery and courier services have grown exponentially, and so has this segment of gig workers.
- To maximise income, workers often have to work long shifts with minimal breaks, some even choosing to “multi-app” to maximise their income. Their well-being was among the issues raised during the National Day Rally in August 2022.
- The problem:
Currently, workers choose their orders instinctively, first-come-first-serve.
Multi-apping is the best way to maximise income and efficiency, yet, there is no single platform solution in Singapore. 
When a worker overcommits, it could result in the inability to meet service delivery standards, financial penalties and fatigue.​

## Screenshots
This portion shows screenshots from the streamlit.io app

![Homepage](https://github.com/hellobiondi/delivery-fasterer-3000/raw/main/screenshots/ss1.png)
*A humble homepage, with a side panel (This idea came from a friend, @lohkokwee)*

![Input data](https://github.com/hellobiondi/delivery-fasterer-3000/raw/main/screenshots/ss2.png)
*Input data was scraped from a list of restaurants; platform, delivery pickup times were randomised, and payout was computed as a function of distance, duration of delivery and some randomness*

![Map of jobs](https://github.com/hellobiondi/delivery-fasterer-3000/raw/main/screenshots/ss3.png)
*Map of jobs available using Leaflet*

![Progress bar](https://github.com/hellobiondi/delivery-fasterer-3000/raw/main/screenshots/ss4.png)
*Tiny progress bar for users to have something to look at while they await results*

![Gantt chart](https://github.com/hellobiondi/delivery-fasterer-3000/raw/main/screenshots/ss5.png)
*Gantt chart for a visualisation of a particular worker's schedule the following day to maximise their earnings. 32 Iterations indicate the 32nd iteration of dynamic job scheduling after the 32 updates of ad-hoc delivery orders. Delivery orders that are committed to, cannot be changed.*

# Set up environment
Get your packages needed installed:

  - On your terminal, navigate to the root file directory
  - `$ pip install -r requirements.txt`
  - or if you want a conda venv, `$ conda env create -f environment.yml`

## Download Data Files

1) Download the following data files from Google Drive at: https://drive.google.com/drive/folders/1xttTjEjQ3pc7KME8xzTneM28q_Gysv5C?usp=sharing
   1) Available Jobs `Jobs.pkl`
   2) Dynamic Jobs `Jobs_dynamic.csv`
   3) Distance-Time Matrix `dist_time_mat.pkl`
   4) Addresses `addresses.csv`
   5) Jobs for Visualisation `Viz_Jobs.csv`
2) Move `Jobs.pkl` and `dist_time_mat.pkl` to the `data` folder and `streamlit\data` folder
3) Move `Jobs_dynamic.csv` to the `heuristic\streaming` folder
4) Move `Viz_Jobs.csv` and `addresses.csv` to the `streamlit\assets` folder

## Starting up Kafka Producer with Docker

Adapted from: https://github.com/mtpatter/time-series-kafka-demo

### Startup instructions:
1) Download and install docker.
2) Open up 2 terminals and `$ cd heuristic\streaming` in each of them.
3) Ensure that `Jobs_dynamic.csv` is in the streaming folder.
4) In terminal 1, run `$ docker compose up --build` to start up Kafka and Zookeeper. 
5) In terminal 2, run `$ docker build -t "kafkacsv" .` to build the kafkacsv docker image.

### Shutdown instructions:
1) In terminal 1, kill the process. Run `$ docker-compose down`.
2) Open a terminal, run `$ docker ps`.
3) For any remaining running container, double-click on the Container ID to highlight it and right-click to copy (no context will show, the text is copied once you right-click on it).
4) Run `$ docker stop <container id>` for each container ID. 

## Running up ALNS with Kafka Producer
1) Open up 2 terminals. 
2) In terminal 1, `$ cd heuristic`.
3) In terminal 2, `$ cd heuristic\streaming`.
4) In terminal 1, run `$ python alns_main.py`.
5) When the output `Topic unknown, creating order-stream topic` appears, go to terminal 2 and run
`$docker run -it --rm -v ${PWD}:/home --network=host kafkacsv python bin/sendStream.py Jobs_dynamic.csv order-stream`. You should see the dynamic jobs streaming in.

## Running up streamlit for visualisation
1. Open up a terminal and change directory to `$ delivery-fasterer-3000/streamlit` folder
2. run `$ streamlit run app.py`
3. Voila!

## Team
This project was done with my teammates, Ruo Xi, Shu Xian, and Li Cheng in fulfilment of our MITB Programme (Artificial Intelligence), and I could never have done it without them!
Notable libraries used were: DOcplex, alns by n-wouda
