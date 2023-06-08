import os, sys
import streamlit as st
from os.path import join, abspath
from static.grader.constants import blank_json

from static.grader.pipeline_photo import photo_pipeline

sys.path.append('./static/grader')
sys.path.append('./static/grader/classes')


left_column, right_column = st.columns([1,1], gap="medium")

left_column.markdown("""**UPLOAD** an image file.""")


with left_column:
    with st.form(key="photo_form"):
        first = st.text_input("First Name", key='first')
        last = st.text_input("Last Name", key='last')
        test_code = st.text_input("Test Code", key='test_code')
        uploaded_image = \
        st.file_uploader(
            key='uploaded_image',
            label="Answer Sheet", 
            type=['png', 'jpg', 'jpeg', 'tif', 'tiff']
        )

        photo_submitted = st.form_submit_button("Upload")

with right_column:
    if photo_submitted:
        answers, half_conf = photo_pipeline(first, last, test_code, uploaded_image)

        right_column.subheader("Confirmation Image")
        st.image(half_conf)

    # set default value for text area
    if 'answers_string' in st.session_state.keys() and st.session_state.answers_string is not None:
        default = st.session_state.answers_string
    else:
        default = blank_json


    with st.form(key="sub_form"):
        st.text_area(label="Scanned Answers", value=default, height=600)
        st.form_submit_button("Submit -- Currently Disabled")







