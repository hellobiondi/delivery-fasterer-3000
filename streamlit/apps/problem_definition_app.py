import streamlit as st

def app():
    # HTML Description

    st.markdown('<h2>Problem Definition & Assumptions</h2>', unsafe_allow_html=True)

    inputs = '''
        <h4><b><u>Input:</u></b></h4>
            <p>
            <ul>
                <li>
                    <b>Planning horizon</b> – rider's shift start-to-end time divided into minute timeslots 0,…,𝑇 where shift start time = 0 and shift end time = 𝑇.
                </li>
                <li>
                    <b>Other Rider inputs</b> – shift start & end location.
                <li>
                    <b>Available Jobs</b> – expected pick-up and delivery timeslots (offset against rider shift start time), pick-up and delivery locations, payout, weight.
                </li>
            </ul>
            </p>
    '''
    st.markdown(inputs, unsafe_allow_html=True)

    outputs = '''
        <h4><b><u>Output:</u></b></h4> Schedule of actual pick-up and delivery timings for each job accepted in the entire shift duration subjected to the following <b><u>constraints</u></b>:
            <p>
            <ol>
                <li>
                    <b>Accepted Jobs</b>
                    <ol type="a">
                        <li>
                            Actual pick-up and delivery times must be within the start and end of the shift as specified by the worker. 
                        </li>
                        <li>
                            Actual pick-up time must be no later than 15min from the expected pickup time.
                        </li>
                        <li>
                            Accepted jobs cannot be cancelled after shift has started.
                        </li>
                        <li>
                            [For dynamic job insertion] Actual pick-up and delivery time must be after current time.
                        </li>
                    </ol>
                </li>
                <li>
                    <b>Schedule</b>
                    <ol type="a">
                        <li>
                            Travel time between two consecutive locations must be less than the time difference on the schedule.
                        </li>
                    </ol>
                </li>
                <li>
                    <b>Capacity</b>
                    <ol type="a">
                        <li>
                            Total weight carried at any point in time cannot exceed the worker's vehicle capacity.
                        </li>
                    </ol>
                </li>
                <li>
                    <b>Worker</b>
                    <ol type="a">
                        <li>
                            Cannot be at two locations at the same time (although he/she can service > 1 job at a time).
                        </li>
                        <li>
                            Must have a minimum rest period of 15 mins after every 2 hours.
                        </li>
                    </ol>
                </li>
            </ol>
            </p>
    '''
    st.markdown(outputs, unsafe_allow_html=True)

    st.write("<h4><b><u>Objective: Maximise total revenue in a single shift</u></b></h4>", unsafe_allow_html=True)
    st.latex("max\sum_{j\in AcceptedJobs}(payout_{j}- penalty_{j}) - totalfuelcost")
    st.latex("totalfuelcost = fuelprice * fuelconsumption * \sum_{i = 0}^{len(Locations)-1}traveldistance_{i, i+1}")
    st.markdown("where <i>Locations</i> is a sequential list of locations that the rider travels to in the schedule. It starts with the shift start location and ends at the shift end location.", True)

    objective2 = '''
            <p>
                Penalty<sub>j</sub> = 50% of the payout for accepted job 𝑗 if the actual delivery time is later than the expected delivery time, else 0.
            </p>
    '''
    st.markdown(objective2, unsafe_allow_html=True)