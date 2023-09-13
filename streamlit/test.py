import streamlit as st
import time
import pandas as pd

st.title("Hello Prof LAU & friends")

st.header("Header")

st.subheader("Subheader")

st.text("Lorem ipsum")

st.markdown("""# h1
## h2
### h3
:moon: <br>
:sunglasses:
**bold**
__italics__""", True)

st.latex("1 + 2 + 3 = 4")

st.write(st)

my_dict = {"members": ['biondi', 'licheng', 'ruoxi', 'shuxian'], 
            "module": ['1', '2', '3', '4']}

df = pd.DataFrame(my_dict)

st.write(my_dict)

st.dataframe(df)

@st.cache_data
def ret_time():
    time.sleep(5)
    return time.time()

if st.checkbox("1"):
    st.write(ret_time())

if st.checkbox("2"):
    st.write(ret_time())

"""
things that can be added:
maps, plots, digraphs, images, videos, audio, dataframes, text/date/time input, radio, selectbox, multi-select, slider, file-upload, sidebar, progress bar, status"""