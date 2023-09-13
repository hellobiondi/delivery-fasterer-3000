""" Frameworks for running multiple Streamlit applications as a single app.
"""
import streamlit as st

class MultiApp:
    """Framework for combining multiple streamlit applications.
    Usage:
        def foo():
            st.title("Hello Foo")
        def bar():
            st.title("Hello Bar")
        app = MultiApp()
        app.add_app("Foo", foo)
        app.add_app("Bar", bar)
        app.run()
    It is also possible keep each application in a separate file.
        import foo
        import bar
        app = MultiApp()
        app.add_app("Foo", foo.app)
        app.add_app("Bar", bar.app)
        app.run()
    """
    def __init__(self):
        self.apps = []

    def add_app(self, title, func):
        """Adds a new application.
        Parameters
        ----------
        func:
            the python function to render this app.
        title:
            title of the app. Appears in the dropdown in the sidebar.
        """
        self.apps.append({
            "title": title,
            "function": func
        })

    def run(self):
        sidebar_desc = '''
            <h1>Delivery Fasterer 3000</h1>
            <h2>Navigation Pane</h2>
                <p>
                    As pages <i><b>do not run concurrently</b></i>, navigating away after the model 
                    returns a result would require the model to re-calculate if you wish to view them again.
                </p>
        '''
        st.sidebar.markdown(sidebar_desc, unsafe_allow_html = True)
        app = st.sidebar.radio(
            ' ',
            self.apps,
            format_func=lambda app: app['title'])
        app['function']()