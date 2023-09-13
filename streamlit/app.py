import streamlit as st

from multiapp import MultiApp
from apps import intro_app, objective_app, problem_definition_app, solution_approach_app, results_app, demo_app

app = MultiApp()

# Navigation
app.add_app("Introduction & Motivation", intro_app.app)
app.add_app("Project Objectives & Scope", objective_app.app)
app.add_app("Problem Definition & Assumptions", problem_definition_app.app)
app.add_app("Solution Approach", solution_approach_app.app)
app.add_app("Demo", demo_app.app)
app.add_app("Results", results_app.app)

# Main App
app.run()