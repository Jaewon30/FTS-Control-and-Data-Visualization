# FTS-Control-and-Data-Visualization

## Project Overview

This project involves developing control and data acquisition/visualization software for a Fourier Transform Spectrometer (FTS) used for optical characterization of materials, filters, and other optical components. The spectrometer supports microwave and sub-millimeter astrophysics, planetary science, and Earth science missions.

The project utilizes two main hardware components:
1. **LabJack U6**: A versatile data acquisition device.
2. **Zaber X-MCB1**: A motor controller for precise movement control.

## Internship Project Description

As an intern at NASA Goddard Space Flight Center, I was helping to commission a Fourier Transform Spectrometer with a cryogenic bolometer system as the detector. My primary task was to develop software for controlling the FTS and analyzing/visualizing the collected data. This software facilitates the control and data collection necessary for the FTS operations.

## Project Date

**Date:** July 2024

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
