import numpy as np
import pandas as pd
import streamlit as st

st.title("Debug App")
st.write("If you can see this, Streamlit backend <-> frontend connection is working.")

st.write("Pandas version:", pd.__version__)
st.write("Numpy version:", np.__version__)

st.line_chart([1, 5, 2, 6, 2, 1])
