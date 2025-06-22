# setup.py

from setuptools import setup, find_packages

setup(
    name="universal-camera-detector",
    version="2.0.0",
    author="Pedro Aglailton",
    description="Detector universal de câmeras Hikvision e Dahua com captura de thumbnail e interface Streamlit",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/pedroaglailton/universal-camera-detector",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "streamlit",
        "requests",
        "pandas",
        "lxml",
        "Pillow",
        "openpyxl",
        "concurrent.futures"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    entry_points={
        "console_scripts": [
            "camera-detector=universal_camera_detector.cli:start_streamlit"
        ]
    }
)
