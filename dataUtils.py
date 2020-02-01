import struct

class DataPacker:
	def __init__(self, lenFormat, headerFormat):
		self.lenStruct = struct.Struct(lenFormat)
		self.headerStruct = struct.Struct(headerFormat)
		self.dataStructs = {}
	
	def pack(self, header, data):
		data = self.dataStructs[header[0]].pack(*data)
		header = self.headerStruct.pack(*header)
		
		allData = header+data
		allData = self.lenStruct.pack(len(allData)) + allData
		
		return allData
	
	def unpack(self, allData):
		header = allData[:self.headerStruct.size]
		data = allData[self.headerStruct.size:]
		
		header = self.headerStruct.unpack(header)
		data = self.dataStructs[header[0]].unpack(data)
		
		return header, data
	
	def addDataStruct(self, dataId, dataFormat):
		self.dataStructs[dataId] = struct.Struct(dataFormat)
		return self
	
	def removeDataStruct(self, dataId):
		del self.dataStructs[dataId]
		return self
	
	def send(self, socket, header, data):
		data = self.pack(header, data)
		
		socket.send(data)
	
	def sendAll(self, sockets, header, data, exceptFor=()):
		data = self.pack(header, data)
		
		for socket in sockets:
			if socket not in exceptFor:
				socket.send(data)
	
	def recv(self, socket):
		length = socket.recv(self.lenStruct.size)
		if length:
			length = self.lenStruct.unpack(length)[0]
			
			allData = socket.recv(length)
			header, data = self.unpack(allData)
			
			return header, data
		else:
			raise NoDataReceivedException

class NoDataReceivedException(Exception):
	pass