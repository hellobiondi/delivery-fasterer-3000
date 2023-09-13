import streamlit as st
from PIL import Image

def app():

    st.image('./assets/delivery_rider_img.jpeg', width=500)

    # HTML Description
    home_intro = '''
        <link rel="stylesheet" href="https://unicons.iconscout.com/release/v4.0.0/css/line.css">
        <h1>Delivery Fasterer 3000</h1>
        <h2>Intro</h2>
            <p>
                This project was conceived in Prof. LAU Hoong Chuin's AI Planning for Decision Making class, at Singapore Management University. On Friday nights.. 7pm, can you imagine?
            </p>
            <p>
                This interactive web application serves as a platform for us to document and demonstrate our entire journey, from ideation to conceptualisation and 
                eventually creating the prototype. Enjoy!
            </p>
        <h2>A Brief Overview</h2>
            <p>
            <ol>
                <li>
                    Demand for food delivery and courier services have grown exponentially, and so has this segment of gig workers.
                </li>
                <li>
                    To maximise income, riders often have to work long shifts with minimal breaks, some even choosing to “multi-app” to maximise their income. Their well-being was among the issues raised during the National Day Rally in August 2022.
                </li>
                <li>
                    <b>The problem:</b>​
                    <ol type="a">
                        <li>
                            Currently, riders choose their orders <u>instinctively</u>, first-come-first-serve.
                        </li>
                        <li>
                            Multi-apping is the best way to maximise income and efficiency, yet, there is <u>no single platform solution</u> in Singapore.
                        </li>
                        <li>
                            When a rider overcommits, it could result in the inability to meet service delivery standards, financial penalties and fatigue.​
                        </li>
                    </ol>
                </li>
                <li>
                    <b>The motivation:</b> help delivery riders to plan a <u>reasonable</u> schedule that maximises their income.
                </li>
            </ol>
            </p>
    '''

    st.markdown(home_intro, unsafe_allow_html=True)
    