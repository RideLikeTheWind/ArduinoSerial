# ArduinoSerial
ArduinoSerial - a simple python script to
read and communicate with Arduino and get feedback
Written by JMascorella
Release under GPL v3.0
Read about it here: https://choosealicense.com/licenses/gpl-3.0/

# Intro
This dirty little solution was written initialy as a terminal app in python
for students to connect some other way than through the serial monitor in the
Arduino IDE, because let's face it, it's limited at best.

The terminal menu isn't great, but it works.

## Essentially, it provides
- A way to set a variety of settings for the board you want to connect to
- A connection protocol for serial data flow, including send and receive so you can 
	teach about data communication
- Threading with queue for events, so it's non-blocking at all stages
- Windows for data viewing

# todo
- Connection and read for data from Adruino
- Store data log to file
- refactor everything using PySimpleGUI