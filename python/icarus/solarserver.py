from threading import Thread
import sys

from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol, listenWS, WebSocketClientProtocol, WebSocketClientFactory, connectWS
from twisted.internet import reactor
from twisted.python import log
import struct
import json

class WSClient(WebSocketClientFactory):

	serverConnection, connected = None, None
	debug = True
	debugCodePaths = True
	oldTilt = 0

	def __init__(self, address, port):
		WebSocketClientFactory.__init__(self, "ws://{0}:{1}".format(address, port), debug=self.debug, origin='null', protocols=["echo-protocol"])

		self.protocol = WSClientProtocol

	def register(self, serverConnection):
		self.serverConnection = serverConnection
		if self.connected:
			self.connected()

	def send(self, msg): #msg = tilt data
		msg = bytes(msg)
		if self.serverConnection:
			print("sending:", msg)
			self.serverConnection.sendMessage(msg, isBinary=False)

	def update(self, tiltInfo, datetime): 
		if not self.serverConnection:
			return

		#tiltInfo = tiltInfo / 100
		#tiltInfo = (0.05 + 0.1 / tiltInfo) - 0.5
		if self.oldTilt == 0:
			self.oldTilt = tiltInfo

		lcd1 = datetime.ljust(16, ' ')
		lcd2 = (str(round(tiltInfo,0))+"%").ljust(16, ' ')
		data = { "tiltPercentage":  round(tiltInfo, 2), "lcd1" : lcd1, "lcd2" : lcd2}
		payload = { "Event" : "update", "Type" : "solar", "att" : data }

		msg = json.dumps(payload)

		print ("delta: ", abs(self.oldTilt - tiltInfo))

		if abs(self.oldTilt - tiltInfo) > 1.235:
			self.oldTilt = tiltInfo
			print("sending...")
			self.send(msg)
		

	def unregister(self):
		self.serverConnection = None

class WSClientProtocol(WebSocketClientProtocol):
	
	debug, debugCodePaths = True, True

	def onConnect(self, response):
		print("Server connected: {0}".format(response.peer))
		return "echo-protocol"

	def onOpen(self):
		print("WebSocket connection open.")
		self.factory.register(self)

	def onMessage(self, payload, isBinary):
		if isBinary:
			print("Binary message received: {0} bytes".format(len(payload)))
		else: #payload is text; convert UTF8 --> Python
			print("Text message received: {0}".format(payload.decode('utf8')))

	def onClose(self, wasClean, code, reason):
		print("WebSocket connection closed: {0}".format(reason))
		self.factory.unregister()
