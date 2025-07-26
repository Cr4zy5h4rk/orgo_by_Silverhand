
import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from solar_calc_streamlit import create_streamlit_app

if __name__ == "__main__":
    create_streamlit_app()
