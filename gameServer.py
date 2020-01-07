import socket
import selectors

class BaseEventHandler:
	@staticmethod
	def on_server_start():
		print("Server started")
	
	@staticmethod
	def on_client_connect(conn):
		print(f"Client connection; Address: {conn.addr}; ID: {conn.id}; Game ID: {conn.game.id}")
	
	@staticmethod
	def on_client_disconnect(conn):
		print(f"Client disconnect; Address: {conn.addr}; ID: {conn.id}; Game ID: {conn.game.id}")
	
	@staticmethod
	def on_data(conn):
		print(f"Data ready to be received; Client ID: {conn.id}")
	
	@staticmethod
	def on_game_create(game):
		print(f"Game created; ID: {game.id}; All game Ids: {game.server.getAllGameIds()}")
	
	@staticmethod
	def on_game_start(game):
		print(f"Game started; ID: {game.id}")
	
	@staticmethod
	def on_game_close(game):
		print(f"Game closed; ID: {game.id}; All game Ids: {game.server.getAllGameIds()}")

class Connection:
	def __init__(self, socket1, server):
		self.socket = socket1
		self.server = server
		self.addr = self.socket.getpeername()
		self.closed = False
		self.id = None
		
		#setup
		self.server.registerConn(self)
		self.autoJoinGame()
		self.server.eventHandlerClass.on_client_connect(self) #run event
	
	def close(self):
		if not self.closed:
			self.closed = True
			self.game.removePlayer(self)
			self.server.unregisterConn(self)
			self.server.eventHandlerClass.on_client_disconnect(self) #run event
			self.socket.close()
	
	def autoJoinGame(self):
		for game in self.server.games:
			if not game.started:
				game.addPlayer(self)
				self.game = game
				return
		
		newGame = self.server.gameClass(self.server)
		newGame.addPlayer(self)
		self.game = newGame
	
	def fileno(self):
		return self.socket.fileno()

class Game:
	def __init__(self, server):
		self.server = server
		self.players = []
		self.started = False
		self.closed = False
		self.id = None
		
		#setup
		self.server.registerGame(self)
		self.server.eventHandlerClass.on_game_create(self) #run event
	
	def close(self):
		if not self.closed:
			self.closed = True
			self.server.unregisterGame(self)
			self.server.eventHandlerClass.on_game_close(self) #run event
			for player in self.players:
				player.close()
	
	def addPlayer(self, conn):
		if not self.started:
			self.players += [conn]
			if len(self.players) == self.server.gameSize:
				self.started = True
				self.server.eventHandlerClass.on_game_start(self) #run event
		else:
			raise Exception("player added to started game")
	
	def removePlayer(self, conn):
		self.players.remove(conn)
		if self.players == [] or self.started:
			self.close()
	
	def sendAll(self, data, exceptFor=()):
		for player in self.players:
			if player not in exceptFor:
				player.socket.send(data)

class NoData(Exception):
	pass

class Server:
	eventHandlerClass = BaseEventHandler
	connClass = Connection
	gameClass = Game
	
	def __init__(self, addr, gameSize):
		self.closed = False
		self.conns = []
		self.connIdCounter = 0
		self.games = []
		self.gameIdCounter = 0
		self.gameSize = gameSize
		
		self.socket = socket.socket()
		self.socket.setblocking(False)
		self.socket.bind(addr)
		
		self.selector = selectors.DefaultSelector()
		self.selector.register(self.socket, selectors.EVENT_READ, self.acceptConn)
	
	def start(self):
		self.eventHandlerClass.on_server_start() #run event
		self.socket.listen()
		while not self.closed:
			events = self.selector.select()
			for key, mask in events:
				callback = key.data
				callback(key.fileobj, mask)
	
	def close(self):
		if not self.closed:
			self.closed = True
			while len(self.conns) != 0:
				self.conns[0].close()
			self.socket.close()
			self.selector.close()
	
	def setEventHandlerClass(self, eventHandlerClass):
		self.eventHandlerClass = eventHandlerClass
		return self
	
	def setConnClass(self, connClass):
		self.connClass = connClass
		return self
	
	def setGameClass(self, gameClass):
		self.gameClass = gameClass
		return self
	
	def registerConn(self, conn):
		conn.id = self.connIdCounter
		self.conns += [conn]
		self.connIdCounter += 1
		self.selector.register(conn, selectors.EVENT_READ, self.readConn)
	
	def unregisterConn(self, conn):
		self.selector.unregister(conn)
		self.conns.remove(conn)
	
	def registerGame(self, game):
		game.id = self.gameIdCounter
		self.games += [game]
		self.gameIdCounter += 1
	
	def unregisterGame(self, game):
		self.games.remove(game)
	
	def getConn(self, connId):
		for conn in self.conns:
			if conn.id == connId:
				return conn
	
	def getGame(self, gameId):
		for game in self.games:
			if game.id == gameId:
				return game
	
	def getAllConnIds(self):
		return tuple(game.id for game in self.conns)

	def getAllGameIds(self):
		return tuple(game.id for game in self.games)
	
	def acceptConn(self, socket1, mask):
		socket2, addr = socket1.accept()
		socket2.setblocking(False)
		
		conn = self.connClass(socket2, self)
	
	def readConn(self, conn, mask):
		try:
			self.eventHandlerClass.on_data(conn) #run event
		except (ConnectionResetError, NoData):
			conn.close()