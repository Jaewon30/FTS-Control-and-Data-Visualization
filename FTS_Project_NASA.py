import time
import u6
import os
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
import threading
import csv
from pathlib import Path
import serial.tools.list_ports
from zaber_motion import Library, Units
from zaber_motion.ascii import Connection, Axis
import traceback
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s") # Logging setup
Library.enable_device_db_store() # Enable Zaber device database store

class Config:
	# Labjack Hardware Constants & File Paths
	raw_data_folder = Path("raw_data")
	raw_data_folder.mkdir(exist_ok=True)
	processed_data_folder = Path("processed_data")
	processed_data_folder.mkdir(exist_ok=True) 
	processed_avg_folder = Path("average_processed_data") 
	processed_avg_folder.mkdir(exist_ok=True) 
	scan_frequency = 1000 # Hz
	bolo_channel = "AIN0" # Analog output channel
	encoder_channel = "AIN200" # Encoder data channel
	
	# Zaber hardware constants
	sweep_length = 50 # mm
	start_point = 0 # mm
	reset_speed = 10 # mm/sec 
	motor_speed = 2 # mm/sec 
	
class LabJackController:
	def __init__(self, device, stop_stream):
		self.device = device
		self.config = Config()
		self.stop_stream = stop_stream
		self.bolo_data = np.array([])
		self.encoder_data = np.array([])
		self.timer = time.time()
		self.start_time = None
		self.end_time = None
		self.poly_remove = Graph().poly_remove
		
	def stream_data(self): # Stream Data from Labjack 
		try:
			logging.info("LabJack U6 Connection Established")
			self.device.getCalibrationData()
			self.device.configIO(TimerCounterPinOffset = 0, NumberTimersEnabled = 2) # Configures IO timers
			self.device.getFeedback(u6.Timer0Config(8), u6.Timer1Config(8)) # Read Quadrature Input timers
			self.device.streamConfig(NumChannels=2, ChannelNumbers=[0, 200], ChannelOptions=[0,0], SettlingFactor=1, ResolutionIndex=5, ScanFrequency=1000)
			self.device.streamStart()
			self.start_time = datetime.now()
			logging.info("Labjack Starting Stream...")
			for packet in self.device.streamData():
				if self.stop_stream.is_set(): 
					break
				if packet["errors"] <= 50 and packet["missed"] <= 50: # If the error and missed from the stream packet doesn't exceed 50 points (acceptable limit)
					self.bolo_data = np.append(self.bolo_data, np.array(packet[self.config.bolo_channel])[2:])
					self.encoder_data = np.append(self.encoder_data, np.array(packet[self.config.encoder_channel])[2:])
			self.device.streamStop()
			self.device.close()
			self.end_time = datetime.now()
			self.encoder_data[self.encoder_data > 17000] = 0 # Set encoder data values above 17000 to zero (Accomadate for tail outlier points)
			logging.info("Stream Completed!")
		except u6.LabJackException as e:
			logging.error(f"LabJack error during streaming: {e}")
		except Exception as e:
			logging.error(f"Unexpected error during streaming: {e}")
	
	def store_data(self): # Store the collected data into a csv file
		try:
			# Store Raw Data
			num_values = len(self.bolo_data)
			duration = self.end_time - self.start_time
			interval_duration = duration / num_values
			interval_start = [str(self.start_time + (interval_duration * i)).replace(":", "-")[11:] for i in range(num_values)]
			interval_end = [str(self.start_time + (interval_duration * (i + 1))).replace(":", "-")[11:] for i in range(num_values)]
			data_dict = {"Start": interval_start, "Mirror Position": self.encoder_data, "Bolometer Data (V)": self.bolo_data, "End": interval_end}
			df_raw = pd.DataFrame(data_dict)
			file_name = self.start_time.strftime("%Y-%m-%d_%H-%M-%S")
			file_path_raw = self.config.raw_data_folder / (file_name + "_raw_data.csv")
			df_raw.to_csv(file_path_raw, index=False)
			logging.info(f"Raw data stored in {file_path_raw}")
			
			# Store Processed Data (poly-removed)
			processed_bolo_data, processed_mirror_steps = self.poly_remove(self.bolo_data, self.encoder_data)
			processed_num_values = len(processed_bolo_data)
			processed_interval_duration = duration / processed_num_values
			processed_interval_start = [str(self.start_time + (processed_interval_duration * i)).replace(":", "-")[11:] for i in range(processed_num_values)]
			processed_interval_end = [str(self.start_time + (processed_interval_duration * (i + 1))).replace(":", "-")[11:] for i in range(processed_num_values)]
			data_dict_processed = {"Start": processed_interval_start, "Mirror Position": processed_mirror_steps, "Bolo Data": processed_bolo_data, "End": processed_interval_end}
			df_processed = pd.DataFrame(data_dict_processed)
			file_path_processed = self.config.processed_data_folder / (file_name + "_processed_data.csv")
			df_processed.to_csv(file_path_processed, index=False)
			logging.info(f"Processed data stored in {file_path_processed}")
		except Exception as e:
			logging.error(f"Error during data storage: {e}")
			
class ZaberController:
	def __init__(self):
		self.config = Config()
		self.connection = None
		self.device = None
		self.axis = None

	def connect_device(self): # Connect to the Zaber Device
		ports = serial.tools.list_ports.comports()
		for port in ports:
			try:
				self.connection = Connection.open_serial_port(port.device)
				device_list = self.connection.detect_devices()
				if device_list:
					self.device = device_list[0]
					logging.info("Zaber Connection Established")
					return
			except Exception as e:
				logging.error(f"Error connecting to the Zaber Device: {e}")

	def configure_axis(self): # Configure Zaber Axis Settings
		try:
			self.axis = self.device.get_axis(1) 
			self.axis.settings.set("maxspeed", self.config.reset_speed, Units.VELOCITY_MILLIMETRES_PER_SECOND) # Set reset speed 
			self.axis.move_absolute(self.config.start_point, Units.LENGTH_MILLIMETRES) # Reset back to the starting point (0 mm)
			self.axis.settings.set("maxspeed", self.config.motor_speed, Units.VELOCITY_MILLIMETRES_PER_SECOND) # Set operational speed
		except Exception as e:
			logging.error(f"Error configuring the axis: {e}")

	def perform_sweep(self, end_stream): # Forward/Backward sweep motion
		try:
			logging.info("Zaber Sweeping forward...") # Move forward
			self.axis.move_relative(self.config.sweep_length, Units.LENGTH_MILLIMETRES)
			logging.info("Zaber Sweeping backward...")
			self.axis.move_relative(-self.config.sweep_length, Units.LENGTH_MILLIMETRES) # Move backward
			logging.info("Sweep Completed!")
			end_stream() # Ends the Labjack stream when the sweep is completed
		except Exception as e:
			logging.error(f"Error during sweeps: {e}")

	def disconnect(self): # Disconnect the device
		if self.connection:
			self.connection.close()
			logging.info("Zaber and Labjack U6 Connection closed\n")

	def __enter__(self): # The Zaber connection is called when execution flow enters the "with" block
		self.connect_device()
		return self 

	def __exit__(self, exception_type, exception_value, traceback): # The disconnection occurs when the execution flow leaves the "with" block
		self.disconnect()

class Graph:
	def __init__(self):
		self.config = Config()

	def plot_current_data(self): # Plot the most recent data collected
		try:
			latest_file = max(self.collect_csv_files(self.config.processed_data_folder), key=os.path.getctime)
			title = latest_file.stem
			processed_mirror_steps, processed_bolo_data = self.read_data(latest_file)
			self.plot(processed_bolo_data, processed_mirror_steps, title)
		except Exception as e:
			logging.error(f"Error plotting current data: {e}")

	def plot_average_data(self): # Plot the average of all collected data
		try:
			all_mirror_steps, all_bolo_data = self.aggregate_data()
			if all_mirror_steps is None or all_bolo_data is None:
				logging.error("No data to plot.")
				return
			avg_processed_bolo_data, avg_processed_mirror_steps = self.poly_remove(all_bolo_data, all_mirror_steps)
			self.store_avg_data(avg_processed_bolo_data, avg_processed_mirror_steps, "Average_Processed_Data_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
			self.plot(avg_processed_bolo_data, avg_processed_mirror_steps, "Average Data")
		except Exception as e:
			logging.error(f"Error calculating average data: {e}")

	def aggregate_data(self): # Aggregate data from all CSV files
		try:
			csv_files = self.collect_csv_files(self.config.raw_data_folder)
			all_mirror_steps = np.array([])
			all_bolo_data = np.array([])
			for csv_file in csv_files:
				mirror_steps, bolo_data = self.read_data(csv_file)
				if mirror_steps and bolo_data:
					all_mirror_steps = np.append(all_mirror_steps, np.array(mirror_steps))
					all_bolo_data = np.append(all_bolo_data, np.array(bolo_data))
			uni_pos = np.unique(all_mirror_steps)
			num_bins = len(uni_pos)
			bolo_avg = np.zeros(num_bins)
			for i in range(num_bins):
				current_pos = uni_pos[i]
				same_pos = np.flatnonzero(all_mirror_steps == current_pos)
				bolo_avg[i] = np.mean(all_bolo_data[same_pos])			
			return uni_pos, bolo_avg  # Return the binned and averaged data
		except Exception as e:
			logging.error(f"Error aggregating data: {e}")
			return None, None

	def collect_csv_files(self, folder):  # Collect all CSV files from the data folder
		csv_files = list(folder.glob("*.csv"))
		if not csv_files:
			raise FileNotFoundError("No CSV files found")
		return csv_files

	def read_data(self, file_path):	 # Read data and timestamps from a CSV file
		try:
			bolo_data = []
			mirror_steps = []
			with open(file_path, "r", newline="") as f:
				reader = csv.reader(f)
				next(reader)  # Skip header
				for row in reader:
					if row:
						mirror_steps.append(float(row[1]))
						bolo_data.append(float(row[2]))
			return mirror_steps, bolo_data
		except Exception as e:
			logging.error(f"Error reading data from file: {e}")
			return [], []

	def poly_remove(self, bolo_data, mirror_steps): # Remove polynomial to acquire interferogram
		try:
			bolo_data = np.array(bolo_data)
			mirror_steps = np.array(mirror_steps)
			poly_deg = 8
			pol_bolo = np.polyfit(mirror_steps, bolo_data, poly_deg)
			pol_func = np.poly1d(pol_bolo)
			bolo_detrended = bolo_data - pol_func(mirror_steps)
			return bolo_detrended, mirror_steps
		except Exception as e:
			logging.error(f"Unexpected error during noise mitigation: {e}")
			return [], []
			
	def plot(self, bolo_data, mirror_steps, title):	# Plot the given data
		try:
			plt.figure(figsize=(10, 6))
			plt.plot(mirror_steps, bolo_data, color="b", linestyle="-", marker="o", markersize=4)
			plt.xlabel("Mirror Position (steps)", fontsize=15)
			plt.ylabel("Voltage (V)", fontsize=15)
			plt.title(f"{title}", fontsize=20)
			plt.grid(True)
			plt.tight_layout()
			plt.show()
		except Exception as e:
			logging.error(f"Error plotting data: {e}")
		
	def store_avg_data(self, bolo_data, mirror_steps, title): # Store the average processed data collection when "Plot Average Data" button is clicked
		try:
			data_dict = {"Mirror Position": mirror_steps, "Bolo Data": bolo_data}
			df_avg = pd.DataFrame(data_dict)
			file_path = self.config.processed_avg_folder / f"{title}.csv"
			df_avg.to_csv(file_path, index=False)
			logging.info(f"Processed average data stored in {file_path}")
		except Exception as e:
			logging.error(f"Error saving processed average data: {e}")

class App:
	def __init__(self):
		self.graph = Graph()
		self.stop_loop = threading.Event() # Thread event for the controller loop
		self.stop_stream = threading.Event() # Thread event to stop the Labjack stream
		self.app = tk.Tk()
		self.setup_gui(self.app)
		
	def setup_gui(self, gui): #Launch GUI
		gui.title("FTS Data Visualization")
		
		#Frames
		main_frame = tk.Frame(gui, padx=20, pady=20)
		main_frame.pack(fill=tk.BOTH, expand=True)
		cur_frame = tk.Frame(main_frame, padx=20, pady=20, relief=tk.RIDGE, borderwidth=2) 
		cur_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
		agg_frame = tk.Frame(main_frame, padx=20, pady=20, relief=tk.RIDGE, borderwidth=2) 
		agg_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

		#Labels
		title_label = tk.Label(main_frame, text="FTS Data Visualization", font=("Arial", 24, "bold"))
		title_label.pack(pady=20)
		cur_label = tk.Label(cur_frame, text="Current Data Captured", font=("Arial", 18))
		cur_label.pack(pady=10)
		agg_label = tk.Label(agg_frame, text="Aggregate Data Average", font=("Arial", 18))
		agg_label.pack(pady=10)
		
		#Buttons
		cur_button = tk.Button(cur_frame, text="Plot Current Data", fg="white", bg="red", font=("Arial", 16), width=20, height=3, command=self.plot_current_data)
		cur_button.pack(pady=20)
		agg_button = tk.Button(agg_frame, text="Plot Average Data", fg="white", bg="blue", font=("Arial", 16), width=20, height=3, command=self.plot_average_data)
		agg_button.pack(pady=20)
		start_button = tk.Button(main_frame, text="Start Data Collection", fg="black", bg="green", font=("Arial", 16), width=25, height=3, command=self.start_data_collection)
		start_button.pack(side=tk.LEFT, pady=20, padx=10)
		stop_button = tk.Button(main_frame, text="Stop Data Collection", fg="black", bg="red", font=("Arial", 16), width=25, height=3, command=self.stop_data_collection)
		stop_button.pack(side=tk.RIGHT, pady=20, padx=10)
		
		gui.mainloop()

	def plot_current_data(self): # Calls the function that plots the current data collection
		self.graph.plot_current_data()

	def plot_average_data(self): # Calls the function that plots the average of all data collection
		self.graph.plot_average_data()

	def start_data_collection(self): # Starts the data collection loop in a thread
		self.stop_loop.clear() # Clear the stop event before starting
		collect_thread = threading.Thread(target=self.data_collection_loop)
		collect_thread.daemon = True # If the gui is closed the program and thread will end
		collect_thread.start()

	def stop_data_collection(self): # Stops the data_collection_loop 
		self.stop_loop.set()

	def data_collection_loop(self): # Loop to continue stream, data collection, and Zaber motor
		counter = 0
		try:
			while not self.stop_loop.is_set(): # While the Stop thread is not set (Stop is activated with the GUI Stop Button)
				counter += 1
				logging.info("Activating Controllers...")
				with ZaberController() as controller: # Calls the ZaberController class with argument as Config()
					if not controller.connection:
						raise Exception("No Connection to Zaber Device")
					controller.configure_axis() # Configure the axis (actuator) of the Zaber Device
					if not controller.axis:
						raise Exception("Zaber Device Axis Not Set")
					self.stop_stream.clear()  # Clear the labjack event before starting a new data collection
					labjack = LabJackController(u6.U6(), self.stop_stream) # Threads the streaming so it can run concurrently with the Motor Sweep
					stream_thread = threading.Thread(target=labjack.stream_data)
					stream_thread.start() # Perform Stream in a Thread
					controller.perform_sweep(self.stop_stream.set) # Perform motor sweep (Stops the Stream once Sweep is completed)
					stream_thread.join() # Ensure the LabJack data collection stops before proceeding
					labjack.store_data() # Store the collected data
					logging.info(f"Completed Data Aquisition #{counter} in Succession")
		except Exception as e:
			logging.error(f"Control Execution Error: {e}")
		logging.info("Data Collection and Motor Stopped.\n")
		
if __name__ == "__main__":
	try:
		App()
	except Exception as e:
		logging.error(f"Error Launching GUI: {e}")