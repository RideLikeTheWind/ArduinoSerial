#/usr/local/bin/python3.8
#
# ArduinoSerial - a simple python script to 
# read and communicate with Arduino and get feedback
# Written by JMascorella
# Release under GPL v3.0
# 
# Read about it here: https://choosealicense.com/licenses/gpl-3.0/
# 

# Requires pySerial, PySimpleGUI
import serial
from serial.tools import list_ports
import PySimpleGUI as sg
#import PySimpleGUIdebugger

# Built in modules
import os
import ast
import time
import threading
import queue
import logging

# Queue for threading
q = queue.Queue()
# For threaded returns
threaded_return_values = []
dirty = False

# Global sg settings
sg.SetOptions(button_color = sg.COLOR_SYSTEM_DEFAULT, text_color = sg.COLOR_SYSTEM_DEFAULT)


#for dirty saving - 5 second debounce so we're not hammering the HDD
def watchCycle():
    global dirty
    while True:
        saveEvent.wait()
        if dirty:
            us.saveFile()
        saveEvent.clear()

global saveEvent
saveEvent = threading.Event()
saveEvent.clear()        
wc = threading.Thread(target=watchCycle, args=(), daemon=True)
wc.start()

# Board setup class
class BoardSetup():
    
    def __init__(self):
        
        self.board_pins = {}
        self.board_connection = ""
        self.baud_rate = 0
    
    def initialSetup(self):
        # Initial setup
        self.setBaud()
        self.setConnection()
        p = input("Do you want to add pins now (y or n)? ")
        if p == "y":
            self.addPins()
        else:
            print("Pins can be added from the main menu later.")
        us.setDirty()
    
    def setBaud(self):
        # Set Baud Rate
        self.baud_rate = input("What is the baud rate for your connection (usually 9600)? ")
        us.setDirty()
        
    def setConnection(self):
        # Set Connection Name
        ports = []
        for comport in serial.tools.list_ports.comports():
            ports.append(comport.device)
            
        print()
        print("-- Connected Ports --")
        i = 1
        for port in ports:
            print(i," :: "+ port)
            i += 1;
        print("-- ---- --")
        # Make this work.... 
        # while True:
#             try:
#                 c = int(input("Which device should we connect to (enter number)? ")) - 1
#             except ValueError:
#                 print("Not a number!")
#             else:
#                 break
        c = int(input("Which device should we connect to (enter number)? ")) - 1
        self.board_connection = ports[c]
        print("Port " + ports[c] + "set")
        
        us.setDirty()
        
    def alterPins(self):
        
        # Alter pins segue to add or remove
        a = input("Do you want to add or remove pins (a/r)? ")
        if a == "a":
            self.addPins()
        if a == "r":
            self.removePins()
    
    def addPins(self) :
        # Obtain settings
        print("Adding devices attached to your Arduino pins...")
        while True :
            pin_name = input("What is the device or input name? ")
            pin_position = input("What is the pin position (1-13 or A1-A6)? ")
            pin_send_value = input("What value should be sent to read data? ")
            self.board_pins[pin_name] = [pin_position, pin_send_value]
            n = input("Add more (y / n)? ")
            
            # No more to add. Print pins for ref.
            if n == "n":
                print("Current pins:")
                for pin_name, pin_values in self.board_pins.items():
                    print("\t Name: " + pin_name + " on pin: " + pin_values[0] + " with send value: " + pin_values[1])
                break
        us.setDirty()
            
    def removePins(self) :
        # For removing pins that may have been created
        if len(self.board_pins) == 0 :
            print("No pins to remove")
            return False 
        
        print("Current pins:")
        for pin_name, pin_values in self.board_pins.items():
            print("\t Name: " + pin_name + " on pin: " + pin_values[0] + " with send value: " + pin_values[1])
        while True:
                
            rm = input("Which pin to remove (type name exactly)? ")
            try:
                self.board_pins.pop(rm)
            except:
                print("No pin by that name.. Sorry!")
            
            #check if pins to remove before proceeding
            if len(self.board_pins) == 0 :
                print("All pins removed!")
                break
                
            # If not done then repeat otherwise break
            d = input("Done (y or n)? ")
            if d == "y":
                break
        us.setDirty()

class userSettings() :
    
    def __init__(self) :
        
        self.file_name = "ArduinoSerial_US.txt"
        self.read_write_values = {}
        
        if not os.path.exists(self.file_name):
            with open(self.file_name, 'w'): pass
            print("Files will be saved to "+self.file_name)
        
    def setDirty(self) :
        # Dirty for saving
        global dirty
        dirty = True
        saveEvent.set()
        
    def saveFile(self) :
        # save settings to file
        global dirty
        
        self.read_write_values["board_connection"] = bs.board_connection
        self.read_write_values["board_pins"] = bs.board_pins
        self.read_write_values["baud_rate"] = bs.baud_rate
        with open(self.file_name, 'w') as f:
            f.write(str(self.read_write_values))
        
        # Return to normal
        dirty = False     
        saveEvent.set()
        
    def readFile(self) :
        
        # Read file for settings
        try:
            with open(self.file_name, 'r') as f:
                s = f.read()
                self.read_write_values = ast.literal_eval(s)
        except:
            return False
        
        # Settings file is empty
        if len(self.read_write_values) == 0 or self.read_write_values == {}:
            return False
            
        bs.board_connection = self.read_write_values["board_connection"]
        bs.board_pins = self.read_write_values["board_pins"]
        bs.baud_rate = self.read_write_values["baud_rate"]
        
        return True

    def currentSettings(self) :
        # Prints current settings
        print("-- Current Settings --")
        print("Baud rate:", bs.baud_rate)
        print("Board connection:", bs.board_connection)
        print("Board Pins: ")
        for pin_name, pin_values in bs.board_pins.items():
            print("\t Name: " + pin_name + " on pin: " + pin_values[0] + " with send value: " + pin_values[1])
        print("-- ---------- --")

class ASMenu() : 
    
    def __init__(self) :
        
        self.menu_options = {
            "1": "Set Baud",
            "2": "Set Connection Name",
            "3": "Edit Pins",
            "4": "Print Settings",
            "5": "Read Data",
            "X": "Exit Program"
        } 
    
    def printMenuOptions(self):
        # Print menu
        print()
        for key, value in self.menu_options.items():
            print(key +" :: "+ value)
    
    def selectMenuOption(self):
        # Select menu option
        self.printMenuOptions()
        so = input("Which option #? ")
        return so

class ASBoard() :

    def __init__(self) :
        
        # Serial settings
        self.ser = serial.Serial()
        self.ser.baudrate = bs.baud_rate
        self.ser.port = bs.board_connection
        self.ser.timeout = 0.5
        
        # timeouts
        # thread timeout
        thread_timeout = 3
        
        #data_refresh timeouts
        self.data_refresh_timeout = 3
        
        self.menu_options = {
            "1": "Read Data (will print data from all current pins)",
            "1a": "Read and log data (stores data in a text file)",
            "2": "Open Connection (for testing)",
            "3": "Close connection (for testing)",
            "4": "Main Menu"
        }
        
    def printMenuOptions(self):
        # prints board menu
        print("----- Board Menu -----")
        for key, value in self.menu_options.items() :
            print(key, " :: ", value)
    
    def selectMenuOption(self):
       # Select menu option
       self.printMenuOptions()
       so = input("Which option #? ")
       return so
    
    def boardMenu(self) :
        while True :
            mo = self.selectMenuOption()
            if mo == "1" :
                self.showData(False)
            if mo == "1a" : 
                self.showData(True)
            if mo == "2" : 
                self.openConnection()
            if mo == "3" : 
                self.closeConnection()
            if mo == "4": 
                print("Return to main menu")
                break
                
    def readData(self) :
        
        #is designed for threaded work only
        # trying to get the queue sorted to thread a queued
        # responder to display data from all pins
            
        for pin_name, pin_values in bs.board_pins.items() :
            q.put([pin_name, pin_values])
            t = threading.Thread(target=self.queueWrapper, args=(q, threaded_return_values))
            t.deamon = True
            t.start()
        
        # Join threads to block main until we refresh
        # Removed as it doesn't improve display performance
        #q.join()
    
    def queueWrapper(self, q, threaded_return_value) :
        while not q.empty():
            work = q.get(timeout=3)
            try:
                logging.info("Serial read requested for device: ", work[0])
                data = self.serialRead(work)
                threaded_return_value.append(data)
            except TypeError:
                logging.info("Empty Serial Read result for device: ", work[0])
                threaded_return_value.append([])
            q.task_done()
        return True
    
    def serialRead(self, work) :
        
        # Setup the variables for comms
        pin = work[0]
        pin_to_read = work[1][0]
        int_to_send = work[1][1]
        
        # Do the actual send
#         self.ser.open()
#         self.ser.write(int_to_send)
#         v = self.ser.read()
#
#         self.ser.close()
        
        # Returns the value read for each pin
        print("Serial Read", pin, pin_to_read, int_to_send)
        # return the hardcoded pin and the
        # result as a raw result
        #return [pin, v]
        
        ## Dummy return for testing
        return [pin, "100oC"]
        
    def showData(self, is_logging) : 
        
        #update button will ping each pin in a loop
        
        #sg.change_look_and_feel('DarkAmber')
        # Window layout
        popupLayout = [
            [sg.Text('Data display window', size=(80, 1))],
            [sg.Text('Waiting for data...', size=(80, 1), key="data_info")],
            [sg.Text('-' * 80)],
            [sg.Text('Data pins', size=(80, 1))]
        ]
        
        for pin_name, pin_values in bs.board_pins.items() :
            popupLayout.append([sg.Text(pin_name, key=pin_name), sg.Text("Data", key=pin_name+"_data")])
        
        popupLayout.append([sg.Button('Close')])
        
        # Create the Window
        window = sg.Window('ARSerial Data Display', popupLayout)
        
        #runs the threads to get the data
        # All initial data calls should be made here and threaded via the queue
        # Data refresh is handled within the main window loop event
        self.readData()
        
        # Event Loop to process "events" and get the "values" of the inputs
        previous_time = time.time()
        while True:
            
            # Read and event watcher
            event, values = window.read(timeout=100)
            if event in (None, 'Close'):	
                # if user closes window or clicks cancel
                break
            
            # Non-blocking call for data refresh
            timeout = time.time()
            if timeout - previous_time >= self.data_refresh_timeout :
                #refresh_data
                self.readData()
                #reset previous_time
                previous_time = time.time()
              
            # Data display within the window
            if threaded_return_values != None:
                message = "Updating data every "+ str(self.data_refresh_timeout)+" seconds"
                window['data_info'].update(message)
                
                if(len(threaded_return_values) > 0):
                    for pin_data in threaded_return_values :
                        window[pin_data[0]+"_data"].update(pin_data[1])
                
                else:
                    # Only used when no data returned - would indicate a timeout
                    window['data_info'].update("Timeout error. Check connections")
                    
        window.close()
        
    def openConnection(self) :
        # Setup connection
        self.ser.baudrate = bs.baud_rate
        
    def closeConnection(self) :
        self.ser.close()
    
    #def readData
    #def storeDataLog
    
########################################
# Run main program
if __name__ == "__main__" :
    
    #PySimpleGUIdebugger.initialize()
    bs = BoardSetup()
    us = userSettings()
    menu = ASMenu()
    
    print("Welcome to the ArduinoSerial Terminal App")
    print("Connect your Arduino with your Computer over Bluetooth.")
    print()
    print("Loading settings...")
    if us.readFile() == False:
        print("No previous settings (or the file was deleted)")
        print("Entering setup...")
        bs.initialSetup()
    
    # Return current setup
    us.currentSettings()
    
    while True:
        if not bs is None and not bs.board_connection is None:
            asb = ASBoard()
            break
        else:
            print("Please provide setup before loading the board settings. Please restart app!")
            break
    
    # Load the main menu
    while True:
        
        option = menu.selectMenuOption()
        
        # Program options
        if option == "1":
            bs.setBaud()
        if option == "2": 
            bs.setConnection()
        if option == "3":
            bs.alterPins()
        if option == "4":
            us.currentSettings()
        if option == "5":
            asb.boardMenu()
            
        # Exit option
        if option == "X":
            #join the background thread in case it is running
            #wc.join()
            # cya!
            break
        
        option == "0"
    # Exit    
    print("Bye!")

########################################EOF