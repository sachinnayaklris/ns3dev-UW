This file describes the other files contained within this folder. 

The configuration file (simulation_config.txt) describes the simulation used to generate the data within this folder.
Values with a -1 are not useful for defining this simulation, but may be used for others. 
Generally locations are given as x, y, z relative to the center of the simulation and 
headings are in radians where 0 means in the positive x direction and pi/2 would be in the positive y direction.
Units are in seconds, meters, meters per second, or hertz.

The configuration file is formatted thusly:
UE Information 
	Information relevant for the movement of the UEs.

BS Information 
	Information describing the base stations and its sectors.

Simulation Paramters 
	Overall parameters such as carrier frequency and sampling rate.

Remaining files, which begin with ULDL_Channel_Response, are the traces of the channel response between a UE and an eNB, 
specified by the trace title. The files are created by simulation with the QuaDRiGa channel simulator and the following additional parameters:
UE height: 1.5m
UE antenna model: dipole
BS Antenna Model: 3gpp-macro
Scenario: Freespace
Transmit power per sector: 46.0206dBm