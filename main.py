import os, sys
import cv2
import streamlit as st
from os.path import join, abspath
from static.grader.constants import blank_json

from static.grader.pipeline import pipeline
from static.grader.pipeline_photo import photo_pipeline

sys.path.append('./static/grader')
sys.path.append('./static/grader/classes')



st.title("ACT Grader")
st.markdown("Upload a scan/photo of the [answer sheet](https://u.pcloud.link/publink/show?code=XZikKEVZFn1FDc3qXGz8v3wWNcqofuqy2M0y), make any necessary corrections, then SUBMIT the answers for grading. You may also download this [demo sheet](), then upload it for grading." )
st.write("You will need the student's first name, last name, and the ACT test code in yyyymm format."
)
st.write(
    "Allowable test codes are 201804, 201806, 201812, 201904, 201906, 202006, 202007, 202012, 202104."
)

left_column, right_column = st.columns([1,1], gap="medium")

left_column.subheader("Upload an Answer Sheet")
left_column.markdown(
    """**UPLOAD** a photo of the answer sheet to update the text field. After the Confirmation image appears, make any necessary corrections, then **SUBMIT** the answers for grading.
"""
)


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


left_column.markdown(
"""If the app is not scanning the photo of your answer sheet, follow these steps.

1. Use this exact [answer sheet](https://u.pcloud.link/publink/show?code=XZikKEVZFn1FDc3qXGz8v3wWNcqofuqy2M0y).
1. Print the answer sheet at 100 dpi or greater. 300-600 dpi is best.
1. Turn on all the lights -- brighter is better.
1. DON'T use a flash.
1. Use a dark background: table, towel, or t-shirt.
1. Make sure all 4 corners of the answer sheet are visible.
1. Make sure that the answer sheet is centered and as even as possible within the image.
1. Make sure that there aren't any shadows on the sheet.
1. Make sure that the all the bubbles and question numbers are clear and legible.
1. Save the image as a png, jpg, or tif file.

"""
)



right_column.subheader("Scanned Answers")

with right_column:
    if photo_submitted:
        ext = uploaded_image.name.split('.')[1]
        PATH_OG = f"static/uploads/{last}_{first}_ACT_{test_code}_Original.{ext}"

        # with open(PATH_OG, 'wb') as f:
            # f.write(uploaded_image.getvalue())

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


# if st.button("Clear Session"):
#     for k in st.session_state.keys():
#         del st.session_state[k]





