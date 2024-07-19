# FTS-Control-and-Data-Visualization

## Project Overview

This project involves developing control and data acquisition/visualization software for a Fourier Transform Spectrometer (FTS) used for optical characterization of materials, filters, and other optical components. The spectrometer supports microwave and sub-millimeter astrophysics missions at NASA Goddard Space Flight Center.

## Internship Project Description

As an intern at NASA Goddard Space Flight Center, I helped to commission a Fourier Transform Spectrometer with a cryogenic bolometer system as the detector. My primary task was to develop software for controlling the FTS and analyzing/visualizing the collected data. This software facilitates the control and data collection necessary for the FTS operations.

## Project Date

**Date:** July 2024

## Background

For this project, the Fourier-Transform Spectrometer was designed as an instrument to analyze the spectral properties of microwave and sub-millimeter radiation. It employs a system of mirrors, with one mirror being movable and the others fixed. When a beam of radiation enters the FTS, it is divided into equal parts by polarizing wire grids. The movable mirror introduces a precise delay in the path of certain wavelengths, leading to wave interference patterns. This setup, along with the fixed mirrors, selectively allows specific wavelengths to pass through while blocking others, creating a detailed interferogram as raw data.

By applying a Fourier Transform to this interferogram, the raw data is converted into a spectrum that reveals the individual wavelength components of the radiation. In this project, data acquisition is achieved through the LabJack U6 device, which reads the analog output from a cryogenic bolometer. The bolometer, connected to the LabJack U6, detects the radiation from the FTS and produces the resulting analog signals. Additionally, the Zaber X-MCB1 motor controller is employed to precisely control the movement of the mirror within the FTS, which is essential for generating interferograms.

## Hardware Components

### LabJack U6
The LabJack U6 is a multifunctional data acquisition device that provides analog and digital input/output capabilities. In this project, it is used to read analog signals from the spectrometer.

### Zaber X-MCB1
The Zaber X-MCB1 is a motor controller used to control the precise movement of the spectrometer's mirror component. It allows for accurate positioning, which is essential for the spectrometer's operation.

## Software Components

### Python Libraries

- **time**: Provides time-related functions to handle timing operations.
- **u6**: Interfaces with the LabJack U6 device to read analog signals.
- **os**: Interacts with the operating system to handle file operations.
- **datetime**: Manages dates and times, useful for timestamping data.
- **pandas**: Analyzes and stores data in dataframes.
- **numpy**: Performs numerical computations and array manipulations.
- **matplotlib**: Creates static graph visualizations.
- **tkinter**: Builds the graphical user interface for the application.
- **threading**: Manages concurrent execution of functions in separate threads.
- **csv**: Reads from and writes to CSV files.
- **pathlib**: Handles filesystem paths.
- **serial.tools.list_ports**: Lists available serial ports for device connections.
- **zaber_motion**: Controls Zaber devices, including motors and stages.
- **traceback**: Provides utilities for extracting and formatting error information.
- **logging**: Outputs log messages to track the application's operation and troubleshoot issues.

### Main Classes and Functions

- **Config**: Configuration class for setting up file paths and hardware constants.
- **LabJackController**: Class for streaming and storing data from the LabJack U6.
- **ZaberController**: Class for controlling the Zaber motor.
- **Graph**: Class for processing and visualizing the data.
- **App**: Class for setting up the GUI and handling user interactions.

## Collaborators

This project would not have been possible without the invaluable support of my following mentors:

- **Thomas Essinger-Hileman**
- **Kyle Helson**
- **Sumit Dahal**

## References

This project utilized several Python libraries and resources:

- **time**: [Python time module documentation](https://docs.python.org/3/library/time.html)
- **u6**: [LabJack U6 Python library documentation](https://labjack.com/support/software/examples/u6)
- **os**: [Python os module documentation](https://docs.python.org/3/library/os.html)
- **datetime**: [Python datetime module documentation](https://docs.python.org/3/library/datetime.html)
- **pandas**: [Pandas documentation](https://pandas.pydata.org/pandas-docs/stable/)
- **numpy**: [NumPy documentation](https://numpy.org/doc/)
- **matplotlib**: [Matplotlib documentation](https://matplotlib.org/stable/contents.html)
- **tkinter**: [Tkinter documentation](https://docs.python.org/3/library/tkinter.html)
- **threading**: [Python threading module documentation](https://docs.python.org/3/library/threading.html)
- **csv**: [Python csv module documentation](https://docs.python.org/3/library/csv.html)
- **pathlib**: [Python pathlib module documentation](https://docs.python.org/3/library/pathlib.html)
- **serial.tools.list_ports**: [PySerial documentation](https://pyserial.readthedocs.io/en/latest/tools.html#module-serial.tools.list_ports)
- **zaber_motion**: [Zaber Motion Library documentation](https://www.zaber.com/software/docs/motion-library/ascii/)
- **traceback**: [Python traceback module documentation](https://docs.python.org/3/library/traceback.html)
- **logging**: [Python logging module documentation](https://docs.python.org/3/library/logging.html)
