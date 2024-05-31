# -*- coding: utf-8 -*-
"""
Name: DeckOPCUAOpConsole.py
This script simulates a Deck OPC UA in real-time or with the desired speedup factor.
@author: Jesús M. Zamarreño

Copyright (C) 2023  Jesús M. Zamarreño

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# import math
import numpy as np
# import plot
import matplotlib.pyplot as plt

# Libreries OPC UA
from opcua import Client
from opcua import ua

#Others
import time as Time

# Define time-related variables
CINT = 1 # 1 time-unit (seconds in this case)
TFIN = 10000 # seconds simulation (if time_units is equal to Seconds)
TSTOP = 0
time_units = "Seconds" # Other options: "Minutes" or "Hours"
fac = 5 # Speedup factor
verbosity = 1  # 0: No verbosity, 1: Verbosity
port = 16701  # Port where deck OPC UA server is listening
 
# Connecting to the OPC UA server
client = Client(f"opc.tcp://localhost:{port}") # If second argument: read/write request timeout

# Connect to deck
while True:
    try:
        client.connect()
    except (ConnectionRefusedError) as error:
        print(f'Se ha producido el error: \'{error}\'.')
    else:
        print('Conexión establecida con el Deck')
        break


# Reset. This makes simulation time equal 0 and default values for simulation variables
command = client.get_node("ns=6; s=command_reset")
command.set_value(ua.Variant(1, ua.VariantType.Int32))

print("Reset done")
Time.sleep(1)

# Run. This runs the experiment for model initialization
command = client.get_node("ns=6; s=command_run")
command.set_value(ua.Variant(1, ua.VariantType.Int32))

print("Run done")
Time.sleep(1)

# Init TIME to 0
var = client.get_node("ns=4; s=TIME")
var.set_value(ua.Variant(0, ua.VariantType.Double))

# Set CINT value to a proper one
var = client.get_node("ns=4; s=CINT")
var.set_value(ua.Variant(CINT, ua.VariantType.Double))

# Set TSTOP value to a proper one
varTSTOP = client.get_node("ns=4; s=TSTOP")
varTSTOP.set_value(ua.Variant(TSTOP, ua.VariantType.Double))

# Set verbosity to a desired value
varVB = client.get_node("ns=7;s=parameter_verbosity")
varVB.set_value(ua.Variant(verbosity, ua.VariantType.Int32))

print("Setting CINT and TSTOP done")
Time.sleep(1)

# Generates number of required integration steps for simulation loop
integration = np.linspace(CINT, TFIN, int(TFIN/CINT))

var = client.get_node("ns=4; s=TIME")
command_integ_cint = client.get_node("ns=6; s=command_integ_cint")

t_calculo_history = []

# Simulation loop
for j in integration:
 
    start = Time.time() # For calculating elapsed time
    
    # Read simulation time
    taux = var.get_value()

    TSTOP = TSTOP + CINT
    varTSTOP.set_value(ua.Variant(TSTOP, ua.VariantType.Double))

    # Integrating one step
    command_integ_cint.set_value(ua.Variant(1, ua.VariantType.Int32))
    
    print("Integ_CINT done")
    
    end = Time.time() # For calculating elapsed time
    t_calculo = end - start # elapsed time in seconds
    t_calculo_history.append(t_calculo)
    print("TIME: " + str(taux) + " - Calculation time: " + str(t_calculo))
    
    CINT_seconds = CINT # default
    if time_units == "Minutes":
        CINT_seconds = CINT*60.0
    elif time_units == "Hours":
        CINT_seconds = CINT*3600.0
        
    if t_calculo>0: # Avoid division by zero
        factor = CINT_seconds/fac/t_calculo
    else:
        factor = 1000
    
    if factor>1: # calculation time has been faster than simulated time
        Time.sleep(CINT_seconds/fac - t_calculo) # for real-time simulation
    else:
        print("Warning: Calculation time longer than real-time")

# Disconnect from server
client.disconnect()

# %%

# Plot some results at the end

plt.plot(t_calculo_history)
plt.title('Calculation time at each time step')
plt.show()

# Plot distribution of calculation times
plt.hist(t_calculo_history, density = True, log = True)
plt.grid(axis = 'y')
plt.title('Distribution of calculation times')
plt.xlabel('Calculation times')
plt.ylabel('Probability density')
plt.show()

# Statistics for t_calculo_history
print(f'Maximum calculation time: {max(t_calculo_history)}')
limit_calculation_time = CINT_seconds/fac
t_gt_limit = len([x for x in t_calculo_history if x > limit_calculation_time])
print(f'{t_gt_limit} time steps where calculation time has been greater than {limit_calculation_time} s')
print(f'Average calculation time: {np.average(t_calculo_history)}')
print(f'Minimum calculation time: {min(t_calculo_history)}')