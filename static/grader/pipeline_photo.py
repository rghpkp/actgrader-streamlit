import os, sys, cv2
import pickle
import argparse
import numpy as np
import streamlit as st
import imageio.v3 as iio
from os.path import join, abspath
from collections import namedtuple
from jinja2 import Environment, FileSystemLoader

sys.path.append('static/grader/classes')
import streamlit as st
from act import ACT
from sheetScanner import Sheet, Bubble
from actSheetScanner import ActSheet
from dewarper import Dewarper
from deshadower import Deshadower

Point = namedtuple('Point', ['x', 'y'])

def photo_pipeline(first, last, test_code, uploaded_image):
    print("\nPipeline\n")

    ### Create file paths
    # first = session.first
    # last = session.last
    # test_code = session.test_code
    # uploaded_image = session.uploaded_image
    ext = uploaded_image.name.split('.')[1]
    f_prefix = f"{last}_{first}_ACT_{test_code}"

    # name_og = session.name_og # Original
    name_og = f"{f_prefix}_Original.{ext}"  # Original
    name_as = f"{f_prefix}_Answer_Sheet.png"  # Dewarped
    name_conf = f"{f_prefix}_Confirmation.png"  # Confirmation
    name_half = f"{f_prefix}_Half_Conf.png"  # Half Size Confirmation
    name_json = f"{f_prefix}_Sub.json"  # Submission json

    PATH_UPLOAD = "static/uploads"
    PATH_TEMP = "static/temporary_files"
    PATH_REF = (join('static/grader/v07-100.png'))
    # PATH_OG = session.PATH_OG
    PATH_OG = (join(PATH_UPLOAD, name_og))
    PATH_AS = (join(PATH_TEMP, name_as))
    PATH_CONF = (join(PATH_TEMP, name_conf))
    PATH_HALF = (join(PATH_TEMP, name_half))
    PATH_JSON = (join(PATH_TEMP, name_json))

    st.session_state['answer_sheet_name'] = name_as
    st.session_state['answer_sheet_path'] = PATH_AS
    st.session_state['confirmation_name'] = name_conf
    st.session_state['confirmation_path'] = PATH_CONF
    st.session_state['half_conf_name'] = name_half
    st.session_state['half_conf_path'] = PATH_HALF
    st.session_state['answers_json_name'] = name_json
    st.session_state['answers_json_path'] = PATH_JSON

    # Read the uploaded image from the bytes buffer
    img = iio.imread(uploaded_image)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    ### Deskew the image
    dw = Dewarper(PATH_REF, img)
    dw.dewarp()
    conf_image = dw.dewarped
    # cv2.imwrite(PATH_AS, dw.dewarped.copy())

    ### Remove shadows and lighting artifacts
    ds = Deshadower(dw.dewarped)
    thr_img = ds.deshadow()
    ### Create the ACT object
    a = ActSheet(thr_img)

    #############################################################################
    section_codes = a.sections.keys()  # ('e', 'm', 'r', 's')

    print("Extracting Section Contours\n-----------------------------------")
    candidates = a.all_contours[0:5]
    for i in range( (len(candidates)-1), -1, -1 ):
        c = candidates[i]
        x,y,w,h = cv2.boundingRect(c)
        area = cv2.contourArea(c)
        ratio = float(w)/float(h)
        # print(f"x = {x}\t y = {y}\t w = {w}  h = {h}\t area = {area}   aspect = {round(ratio,5)}")

        for code in section_codes:
            wasFound = a.extract_section_area(a.sections[code], c)

            if wasFound is not None:
                # print(f"Found {a.section_labels[code]} section")
                # a.show_contours(a.image, f"{a.section_labels[code]} Section", 
                #                 [a.sections[code].enclosing_contour], 2)
                del(candidates[i])
                continue
    

    for code in a.sections.keys():
        if a.sections[code].sheet is None:
            # print(f"The {s.section_labels[code]} section was not found. Exiting.")
            sys.exit()
            # @TODO replace the exit with new method calls passing relaxed filter
            # params or another extract_contours call with modded params
        else:
            pass

    print("SUCCESS: All 4 sections extracted \n")


    # Extract interior contours and convert them to bubbles
    for code, section in a.sections.items():
        sLabel = a.section_labels[code]

        # print("\nEXTRACTING BUBBLES \n")
        # print(f"\n{sLabel} Section \n----------------------------------")

        s = section.sheet
        contours = s.contours_from_section(s.image, s.all_contours[0])
        contours = s.extract_circles(contours, 100, 0.5)

        bp = ((14,16), (14,16), (0.9,1.1), 0.7)  # bubble parameters
        bubbles = s.contours_to_bubbles(contours, bp[0], bp[1], bp[2], bp[3])
        section.bubbles = bubbles

        # Build the section maps
        sMap = s.build_sectionMap(bubbles, section.grid, section.num_questions, section.group_length)
        section.sectionMap = sMap

        # Generate the indices 
        # print(f"\nGenerating {sLabel} Indices \n--------------------------------------")
        indices = s.generate_filled_indices(sMap, section.mask_shape, 
                                                section.white_epsilon, 
                                                section.filter_params, False)
        section.answer_indices = indices


        # Show the confirmation rectangles for the section
        confirmation = s.get_section_confirmation(sMap, section.answer_indices)
        section.confirmation_points = confirmation

        for fLabel in ('adaptive', 'maximum', 'threshold'):
            conf = confirmation[fLabel]
            conf_label = str.join(' ', (sLabel, fLabel))
            conf_img = s.show_section_confirmation(s.image, conf, (14,14))

        

    a.conf_pts = a.get_sheet_confirmation('maximum')
    conf_img = a.show_sheet_confirmation(dw.dewarped, a.conf_pts, (14,14), False, "")
    half_conf = cv2.resize(conf_img, (425, 550), interpolation=cv2.INTER_AREA)
    half_conf = cv2.cvtColor(half_conf, cv2.COLOR_BGR2RGB)
    # cv2.imshow("Half Conf", half_conf)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # cv2.imwrite(PATH_CONF, conf_img)
    # cv2.imwrite(PATH_HALF, half_conf)

    # Convert answer indices to a submission dict
    submission = a.indices_to_submission(None, test_code, first, last)

    # Write the json
    j = a.submission_to_json(submission)


    # print("Writing submission to json file")
    # with open(PATH_JSON, 'w') as f:
        # print(j, file=f)
   
    st.session_state['answers_string'] = j
    st.session_state['half_conf'] = half_conf

    return j, half_conf 

