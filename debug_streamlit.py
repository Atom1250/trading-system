import streamlit as st
import pandas as pd
import numpy as np

st.title("Debug App")
st.write("If you can see this, Streamlit backend <-> frontend connection is working.")

st.write("Pandas version:", pd.__version__)
st.write("Numpy version:", np.__version__)

st.line_chart([1, 5, 2, 6, 2, 1])
