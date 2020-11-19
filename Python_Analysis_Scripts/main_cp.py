#!/usr/bin/python




#the goal of the script is to write both the  mid and high level data processing files
#
#mid level processing files:
#Data Rate (bytes/s) (note 1) (1 file per UE), title (example) = dataRate,UE1,binWidth$binWidth.csv
#eNb association over time (note 1) (note 2) (1 file per UE), title (example) = eNbAssociation,UE1.csv
#RSRP over time (note 3) (1 file per UE), title (example) = RSRP,UE1.csv
#RSRQ over time (note 3) (1 file per UE), title (example) = RSRQ,UE1.csv
#
#note 1: Each trial will get a copy of each of these files. The file will be formatted as two lines. The first line is the 
#time axis, second line is the performance indicator, defined by the file title. The top level scenario folder will also 
#recieve an averaged version of this metric. the averaged version of these files will be formatted as first line = time, 
#second line = performance indicator, final line = 95% confidence interval (even bounds).
#
#note 2: This trace will not have an average, averaging this data makes no sense.
#
#note 3: Each trial will get a copy of each of these files. The file will be formatted as 3*numBS + 1 lines. The first line is the 
#time axis, the subsequent lines will be the rsrp/rsrq traces. line N indicates the trace comes from eNb ceil((N-1)/3), sector ((N-1) - 1) % 3 
#The top level scenario folder will also recieve an averaged version of this metric. The averaged version will be formatted as first line = time, 
#final line = 95% confidence interval (even bounds), starting with line 2 every other line will be the average value of the rsrp/rsrq
#across all trials over time and starting line 3 every other line will be the 95% confidence interval (even bounds).
#
#the top level scenario folder (the folder which contains each trial folder) will contain a version of each of these data files
#which has averaged appended to the title name which will be defined as the average of the relevant performance indicator for all trials
#and will be formatted as first line = time, line 2 to end-1 = performance indicator, final line = 95% confidence interval (even bounds).
#
#high level files:
#TBD on the exact formatting but it will be a record of ping pong ratio and too-early/too-late ratio

import sys
import math
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats
import os
import csv

scenario = "Scenario" + sys.argv[1]
HystVal = float(sys.argv[2])
TTT = float(sys.argv[3])
trials = int(sys.argv[4])

#find some parameters via the config file
print("Determining Configuration Parameters")
configData = {}
with open("/data/sachin/ns-3-dev-git/exampleTraces/simulation_config.txt") as config:
	config_line = config.readline()
	while config_line:
		temp = config_line.split(':')
		if len(temp) == 2:
			if len(temp[1].split(' ')) == 2:
				configData[temp[0]] = float(temp[1])
			else:
				temp2 = temp[1].split(' ')
				configData[temp[0]] = [float(i) for i in temp2[1:len(temp2)]]
		config_line = config.readline()


numUE = int(configData["number of UEs"])
numBS = int(configData["number of BS"])
simuationDuration = configData["Simulation duration (s)"]
samplingFrequency = configData["Sampling Frequency (Hz)"]


#load in the files, two of relevance, 'lte-tcp-x2-handover.ue-measurements.dat' and 'lte-tcp-x2-handover.tcp-receive.dat'

#creating the variables
print("Loading Data")
rsrpRsrqTime = []
rsrpData = []
rsrqData = []
currentServingCell = []
packetData = []

for i in range(trials):
	rsrpRsrqTime.append([])
	currentServingCell.append([])
	rsrpData.append([])
	rsrqData.append([])
	packetData.append({})
	for j in range(numBS):#initialize the rsrp/rsrq data dicts with numBS*3 values (3 sectors for each BS)
		rsrpData[i].append([])
		rsrqData[i].append([])
		for k in range(3):
			rsrpData[i][j].append([])
			rsrqData[i][j].append([])


#load in the data from each trial separately
lineCounter = 0
resultsHome = "/data/sachin/ns-3-dev-git/results/"
for i in range(trials):
	print("     Trial " + str(i+1))
	#first load the RSRP/RSRQ measurements
	scenarioFolder = scenario + "-" + str(int(HystVal)) + "-" + str(int(TTT)) + "/" + scenario + "-" + str(int(HystVal)) + "-" + str(int(TTT)) + "-" + str(i+1) + "/"
	rsrpRsrqFilename = "lte-tcp-x2-handover.ue-measurements.dat"
	with open(resultsHome + scenarioFolder + rsrpRsrqFilename) as rsrpRsrqFile:
		rsrpRsrq_line = rsrpRsrqFile.readline()
		rsrpRsrq_line = rsrpRsrqFile.readline()#first line is just the header, skip it
		while rsrpRsrq_line:
			temp = rsrpRsrq_line.split()
			time = float(temp[0])
			cellID = int(temp[2])
			servingCellFlag = int(temp[3])
			currentRsrp = float(temp[4])
			currentRsrq = float(temp[5])

			if cellID == 1:#not(int(1000*time) in [int(1000*x) for x in rsrpRsrqTime[i]]):
				rsrpRsrqTime[i].append(time)

			rsrpData[i][int(math.ceil((cellID)/3)-1)][int(((cellID - 1) % 3))].append(currentRsrp)
			rsrqData[i][int(math.ceil((cellID)/3)-1)][int(((cellID - 1) % 3))].append(currentRsrq)

			if servingCellFlag == 1:
				currentServingCell[i].append(cellID)
			lineCounter = lineCounter + 1
			rsrpRsrq_line = rsrpRsrqFile.readline()

	#next the packet data
	packetFilename = "lte-tcp-x2-handover.tcp-receive.dat"
	with open(resultsHome + scenarioFolder + packetFilename) as packetFile:
		packet_line = packetFile.readline()
		packet_line = packetFile.readline()
		while packet_line:
			temp = packet_line.split()
			time = temp[0]
			bytesRx = int(temp[1])
			if time in packetData[i]:
				packetData[i][time] = packetData[i][time] + bytesRx
			else:
				packetData[i][time] = bytesRx
			packet_line = packetFile.readline()




#from here we will do some smoothing on the recieve packet data to get data rate. Packet arrivals are binned together based upon the variable
#binWidth, the data rate at the center of each bin is equal to the number of packets which arrive in that bin divided by binWidth. increasing binWidth
#acts to smooth the data rate. an actual moving average filter can't be used because the packet arrivals arent uniformly sampled. another potential
#technique would be to force uniform sampling by inserting 0 every millisecond which doesnt have a packet arrival then using a moving average filter.
#such a technique would result in a data rate trace with more data rate points but the same issues with oversmoothing present in the binning method.
#the binning method used here is approximately identical a downsampled version of the moving average method described above.
"""
print("Finding Data Rate")
dataRate = []
dataRateTime = []


for i in range(trials):
	dataRate.append([])
	dataRateTime.append([])

binWidth = 60*.001;


for i in range(trials):
	print("     Trial " + str(i+1))
	packetTime = [float(x) for x in packetData[i].keys()]
	temp = list(range(int(1000*(packetTime[0]+binWidth/2)),int(1000*(packetTime[-1]-binWidth/2)),int(1000*binWidth)))#converted to integers for range
	dataRateTime[i] = [i/1000 for i in temp]#converted back to floats
	recievedBytes = list(packetData[i].values())
	for j in range(len(dataRateTime[i])):
		binTimestamps = [x for x in packetTime if abs(x - dataRateTime[i][j]) < binWidth/2]
		binTimestampIndexes = [packetTime.index(x) for x in binTimestamps]
		dataRate[i].append(sum([recievedBytes[x]/binWidth for x in binTimestampIndexes]))
"""








"""
#first find the averaged values (only do this if there is more than 1 trial)
if trials > 1:
	print("Finding Averages of Performance Indicators")

	averageDataRateTime = []
	averageDataRate = []
	dataRateConfidenceInterval = []
	for i in range(len(dataRateTime[0])):
		#first is data rate
		#grab the ith value 
		#this is a sloppy way of doing things but will work for a first draft, it presumes that the packet arrivals begin and end at the same
		#time for all files, which isnt nescesarily the case
		tempTime = [x[i] for x in dataRateTime]
		tempData = [x[i] for x in dataRate]
		averageDataRateTime.append(sum(tempTime)/len(tempTime))
		averageDataRate.append(sum(tempData)/len(tempData))
		tempDataArray = 1.0 * np.array(tempData)
		std = scipy.stats.sem(tempDataArray)
		CI = std * scipy.stats.t.ppf((1 + .95)/2.,trials-1)
		dataRateConfidenceInterval.append(CI)


	averageRsrpRsrqTime = []
	averageRsrp = []
	averageRsrq = []
	rsrpConfidenceInterval = []
	rsrqConfidenceInterval = []

	for i in range(numBS):
		averageRsrp.append([])
		averageRsrq.append([])
		rsrpConfidenceInterval.append([])
		rsrqConfidenceInterval.append([])
		for j in range(3):
			averageRsrp[i].append([])
			averageRsrq[i].append([])
			rsrpConfidenceInterval[i].append([])
			rsrqConfidenceInterval[i].append([])





	for i in range(len(rsrpRsrqTime[0])):
		#next RSRP/RSRQ/CellID, this has to be done in a separate for loop as the lengths are different
		#this is less sloppy than for the data rate, the timestamps for all RSRP/RSRQ/CellID measurements should be identical
		tempTime = [x[i] for x in rsrpRsrqTime]
		averageRsrpRsrqTime.append(sum(tempTime)/len(tempTime))

		for j in range(numBS):
			for k in range(3):
				tempRSRP = [x[j][k][i] for x in rsrpData]
				tempRSRQ = [x[j][k][i] for x in rsrqData]

				averageRsrp[j][k].append(sum(tempRSRP)/len(tempRSRP))
				averageRsrq[j][k].append(sum(tempRSRQ)/len(tempRSRQ))
				
				tempRsrpArray = 1.0 * np.array(tempRSRP)
				std = scipy.stats.sem(tempRsrpArray)
				CI = std * scipy.stats.t.ppf((1 + .95)/2.,trials-1)
				rsrpConfidenceInterval[j][k].append(CI)

				tempRsrqArray = 1.0 * np.array(tempRSRQ)
				std = scipy.stats.sem(tempRsrqArray)
				CI = std * scipy.stats.t.ppf((1 + .95)/2.,trials-1)
				rsrqConfidenceInterval[j][k].append(CI)
"""




#start with writing the files for each trial
home = os.getcwd()

for i in range(trials):
	scenarioFolder = scenario + "-" + str(int(HystVal)) + "-" + str(int(TTT)) + "/" + scenario + "-" + str(int(HystVal)) + "-" + str(int(TTT)) + "-" + str(i+1) + "/"
	os.chdir(resultsHome + scenarioFolder)


	#data rate
	temp = [dataRateTime[i],dataRate[i]]
	file = open('dataRate,UE' + str(1) + ',binWidth' + str(binWidth) + '.csv', 'w+', newline ='') #the UE ID will need to be fixed in the future
	with file:
		write = csv.writer(file)
		write.writerows(temp)


	#RSRP over time
	temp = [rsrpRsrqTime[i]]
	for j in range(numBS):
		for k in range(3):
			temp.append(rsrpData[i][j][k])
	file = open('RSRP,UE' + str(1) + '.csv', 'w+', newline ='') #the UE ID will need to be fixed in the future
	with file:
		write = csv.writer(file)
		write.writerows(temp)


	#RSRQ over time
	temp = [rsrpRsrqTime[i]]
	for j in range(numBS):
		for k in range(3):
			temp.append(rsrqData[i][j][k])
	file = open('RSRQ,UE' + str(1) + '.csv', 'w+', newline ='') #the UE ID will need to be fixed in the future
	with file:
		write = csv.writer(file)
		write.writerows(temp)


	#cellID
	temp = [rsrpRsrqTime[i],currentServingCell]
	file = open('currentServingCell,UE' + str(1) + '.csv', 'w+', newline ='') #the UE ID will need to be fixed in the future
	with file:
		write = csv.writer(file)
		write.writerows(temp)












"""

#now write the averages
scenarioFolder = scenario + "-" + str(int(HystVal)) + "-" + str(int(TTT))
os.chdir(resultsHome + scenarioFolder)
#data rate
temp = [averageDataRateTime,averageDataRate,dataRateConfidenceInterval]
file = open('AveragedataRate,UE' + str(1) + ',binWidth' + str(binWidth) + '.csv', 'w+', newline ='') #the UE ID will need to be fixed in the future
with file:
	write = csv.writer(file)
	write.writerows(temp)


#RSRP over time
temp = [averageRsrpRsrqTime]
for j in range(numBS):
	for k in range(3):
		temp.append(averageRsrp[j][k])
		temp.append(rsrpConfidenceInterval[j][k])
file = open('AverageRSRP,UE' + str(1) + '.csv', 'w+', newline ='') #the UE ID will need to be fixed in the future
with file:
	write = csv.writer(file)
	write.writerows(temp)


#RSRQ over time
temp = [averageRsrpRsrqTime]
for j in range(numBS):
	for k in range(3):
		temp.append(averageRsrq[j][k])
		temp.append(rsrqConfidenceInterval[j][k])
file = open('AverageRSRQ,UE' + str(1) + '.csv', 'w+', newline ='') #the UE ID will need to be fixed in the future
with file:
	write = csv.writer(file)
	write.writerows(temp)
"""



os.chdir(home)








"""
plt.plot(rsrpRsrqTime[0],rsrpData[0][0][0],label="eNb1,sector1")
plt.plot(rsrpRsrqTime[0],rsrpData[0][0][1],label="eNb1,sector2")
plt.plot(rsrpRsrqTime[0],rsrpData[0][0][2],label="eNb1,sector3")
plt.plot(rsrpRsrqTime[0],rsrpData[0][1][0],label="eNb2,sector1")
plt.plot(rsrpRsrqTime[0],rsrpData[0][1][1],label="eNb2,sector2")
plt.plot(rsrpRsrqTime[0],rsrpData[0][1][2],label="eNb2,sector3")
plt.plot(averageRsrpRsrqTime,averageRsrp[0][0],label="average")




tempTime = [sum(x)/2 for x in zip(dataRateTime[0],dataRateTime[1])]
tempData = [sum(x)/2 for x in zip(dataRate[0],dataRate[1])]
plt.plot(dataRateTime[0],dataRate[0],label="trial1")
plt.plot(dataRateTime[1],dataRate[1],label="trial2")
plt.plot(averageDataRateTime,averageDataRate,label="average")

plt.plot(averageDataRateTime,dataRateConfidenceInterval,label="CI")
plt.legend()
plt.show()
"""










