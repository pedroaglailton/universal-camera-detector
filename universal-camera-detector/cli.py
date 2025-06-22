# universal_camera_detector/cli.py

import streamlit.cli
import sys

def start_streamlit():
    sys.argv = ["streamlit", "run", "app.py"]
    sys.exit(streamlit.cli.main())
