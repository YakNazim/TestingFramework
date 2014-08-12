import socket
import time
import subprocess
import csv
import thread
from collections import defaultdict

class SendReceiveLibrary:		
	def sim_format(self, lld, data):
  		return '%s\t%s\n' % (lld , data.encode('hex'))

	def send_to_driver(self, fileName, fileDesc, driver, lock):
		conn = socket.fromfd(fileDesc, socket.AF_INET, socket.SOCK_STREAM)
    		file = open(fileName,"rb")
		file = csv.reader(file, delimiter = '\t')
		lastTime = 0.0
		for row in file:
			newTime = float(row[1])
			if ((newTime - lastTime) > 0.0):
				print "time to wait: ", (newTime - lastTime), " seconds"
				time.sleep(newTime - lastTime)
        		conn.send(self.sim_format(driver, row[0]))
			lastTime = newTime
			print "sent: ", row[0], " to ", driver
		conn.send(self.sim_format(driver, "end"))

	def send_and_receive(self, port, fileName, *apps):
		HOST = ''    		  
		PORT = int(port)
		lock = thread.allocate_lock()           
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind((HOST, PORT))
		s.listen(1)
		filesToRead = 0
		activeApps = []
		data = defaultdict(list)

		for appName in apps:
			activeApps.append(subprocess.Popen(appName, stdout=subprocess.PIPE))

		conn, addr = s.accept()
		print "connection accepted on: ", addr

		file = open(fileName,"rb")
		file = csv.reader(file, delimiter = '\t')
		for row in file:
			thread.start_new_thread(self.send_to_driver, (row[0], conn.fileno(), row[1], lock))
			filesToRead += 1
		while (1):
			message = conn.recv(1024)
      			header, code = message.strip().split('\t', 1)
      			dataChunk = code.decode('hex')
			if (dataChunk == "end"):
				filesToRead -= 1
				if (filesToRead <= 0):
					print "ending..."
					break
			else:
				data[header].append(dataChunk)
			print "received: ", dataChunk, " from ", header
			
		for app in activeApps:		
			app.terminate()
		conn.close()
		s.close()
		return data

	def echo_test(self, data, fileName):
		dataString = ""
    		file = open(fileName,"rb")
		file = csv.reader(file, delimiter = '\t')
		fileContent = ""
		for row in file:
			fileContent += row[0]
		for dataChunk in data['SD1_IO']:
			dataString += dataChunk
		if not fileContent == dataString:
			raise AssertionError("Data sent did not match data received")
		else:
			print "Test passed!"

