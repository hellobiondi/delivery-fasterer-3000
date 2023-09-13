import streamlit as st

def app():
    # HTML Description
    solution_approach = '''
        <h2>Solution Approach</h2>
        <h4><b><u>Day ahead Scheduling</u></b></h4>
            <p>
            <ol>
                <li>
                    Adaptive Large Neighbourhood Search
                </li>
                <li>
                    Initial solution construction
                </li>
                <li>
                    Repair and destroy operators
                </li>
                <li>
                    Lambda and omegas
                </li>
            </ol>
            </p>
        
        <h4><b><u>Dynamic Scheduling</u></b></h4>
            <p>
            <ol>
                <li>
                    Does not remove jobs from the day-ahead schedule (worker cannot cancel a job that he/she has committed to)
                </li>
                <li>
                    Check if the insertion of the new job is feasible
                </li>
            </ol>
            </p>
    '''
    st.markdown(solution_approach, unsafe_allow_html=True)