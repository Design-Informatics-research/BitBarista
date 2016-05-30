#!/usr/bin/env python
import time
import os
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
DEBUG = 0

# change these as desired - they're the pins connected from the
# SPI port on the ADC to the Cobbler
SPICLK = 18
SPIMISO = 23
SPIMOSI = 24
SPICS = 25

# set up the SPI interface pins
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)

CHANNEL_NAMES = ["serbatoio","al_fondi","al_generico","al_calcif","premacinato","tazza1","tazza2","vapore"]

#MCP Channel to Control Mappings
# serbatoio   #pin 10
# al_fondi    #pin 12
# al_generico #pin 14
# al_calcif   #pin 16
# premacinato #pin 18
# tazza1      #pin 21
# tazza2      #pin 23
# vapore      #pin 25

# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
  if ((adcnum > 7) or (adcnum < 0)):
          return -1
  GPIO.output(cspin, True)

  GPIO.output(clockpin, False)  # start clock low
  GPIO.output(cspin, False)     # bring CS low

  commandout = adcnum
  commandout |= 0x18  # start bit + single-ended bit
  commandout <<= 3    # we only need to send 5 bits here
  for i in range(5):
          if (commandout & 0x80):
                  GPIO.output(mosipin, True)
          else:
                  GPIO.output(mosipin, False)
          commandout <<= 1
          GPIO.output(clockpin, True)
          GPIO.output(clockpin, False)

  adcout = 0
  # read in one empty bit, one null bit and 10 ADC bits
  for i in range(12):
          GPIO.output(clockpin, True)
          GPIO.output(clockpin, False)
          adcout <<= 1
          if (GPIO.input(misopin)):
                  adcout |= 0x1

  GPIO.output(cspin, True)
  
  adcout >>= 1       # first bit is 'null' so drop it
  return adcout


def read_state():
  state = {"overall":"","serbatoio":"", "al_fondi":"", 
    "al_generico":"", "al_calcif":"", "premacinato":"", 
    "tazza1":"","tazza2":"","vapore":""}

  # 100 readings x 0.0005 pause = 0.05 
  # flash cycle = 6 * 0.05
  # on for 0.15, off for 0.15
  results = []

  results.append(collect_readings())
  results.append(collect_readings())
  results.append(collect_readings())
  results.append(collect_readings())
  results.append(collect_readings())
  results.append(collect_readings())

  print time.time(),
  all_channel_averages = []
  sample = 0
  while sample < len(results):
    avg = sum(results[sample])/len(results[sample])
    print avg,
    all_channel_averages.append(avg)
    sample+=1
  
  #test if machine is off
  all_off=False
  is_steady=test_steady(all_channel_averages)
  all_off=test_hi_spread(all_channel_averages)
  
  if not all_off:
    all_off = test_hival(results)
  
  if all_off:
    state["overall"] = 'off'
  elif is_steady:
    state["overall"] = 'steady'
  else:
    state["overall"] = 'other'
  
  print state["overall"]

  return state

def test_steady(averages):
  #is avg steady - ie no flashing
  if abs(max(averages) - min(averages)) <= 1.5:
    return True
  else:
    return False

def test_hi_spread(averages):
  #is there a lot of fluctuation?
  if abs(max(averages) - min(averages)) >= 40:
    return True
  else:
    return False

def test_hival(results):
  #do we have any super high values?
  sample = 0
  while sample < len(results):
    i=0
    while i <= 7:
      if results[sample][i] > 100: 
        return True
      i+=1
    sample+=1
  return False

def collect_readings():
  channel_names      = CHANNEL_NAMES
  channel_readings   = [[],[],[],[],[],[],[],[]]
  channel_averages   = []

  #collect 100 readings for each channel
  x=0
  while x <= 100:
    channel = 0
    while channel <= 7:
      channel_value = readadc(channel, SPICLK, SPIMOSI, SPIMISO, SPICS) # read the analog pin
      channel_value = channel_value / 10.24 # convert 10bit adc0 (0-1024) trim pot read into 0-100 value
      channel_readings[channel].append(channel_value)
      channel+=1
    x+=1
    time.sleep(0.0005)

  #build hash with average from readings for each channel
  channel = 0 
  while channel <= 7:
    channel_average = sum(channel_readings[channel])/len(channel_readings[channel])
    channel_average = round(channel_average, 2)
    channel_averages.append(channel_average)
    channel+=1

  return channel_averages


def log_results():
  channel_names = CHANNEL_NAMES
  while True: 
    results = collect_readings()
    print time.time(),
    channel = 0
    while channel <= 7:
      #print ",",channel_names[channel], 
      print ",",results[channel],
      if (channel==7):
        print ""
      channel+=1

def log_state():
  while True:
    read_state()