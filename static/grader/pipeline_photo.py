import os, sys, cv2
import pickle
import argparse
import numpy as np
import streamlit as st
import imageio.v3 as iio
from os.path import join, abspath
from collections import namedtuple

Point = namedtuple('Point', ['x', 'y'])

def photo_pipeline(first, last, test_code, uploaded_image):
    print("\nPipeline\n")

    # Code omitted for privacy

    return """{'json':'string'}""", np.eye(400)

