import streamlit as st

def app():
    # HTML Description

    st.image('./assets/pickupp-user.jpeg', width=500)

    objectives = '''
        <h2>Project Objectives & Scope</h2>
            <p>
            <ol>
                <li>
                    <b>Objective:</b> Develop a <u>worker-centric scheduling tool for a <b>single worker</b></u> that maximises the driver’s daily earnings while
                    <ol type="a">
                        <li>
                            Planning around the worker’s preferences.
                        </li>
                        <li>
                            Not violating constraints on service delivery standards and the worker’s well-being.
                        </li>
                    </ol>
                </li>
                <li>
                    <b>Scope:</b>
                    <ol type="a">
                        <li>
                            Parcel delivery scenario for drivers
                            <ol type="i">
                                <li>
                                    Day-before planning (once committed, cannot cancel the jobs else it will affect worker’s performance ratings)
                                </li>
                                <li>
                                    Dynamic ad-hoc insertion of new jobs along the day
                                </li>
                            </ol>
                        </li>
                        <li>
                            Focus on a <u>single worker</u> since this is meant to be a personal tool.
                        </li>
                        <li>
                            Across <u>one or more platforms</u> (to simulate a multi-apping scenario)
                        </li>
                    </ol>
                </li>
                <li>
                    <b>Benefits:</b> The ability to generate superior solutions (over instinctive choice) may encourage delivery companies to expose some jobs to third-party demand/supply aggregators to support multi-apping.
                </li>
            </ol>
            </p>
    '''
    st.markdown(objectives, unsafe_allow_html=True)
