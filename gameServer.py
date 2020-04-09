import socket
import selectors

class BaseEventHandler:
	def server_start(self):
		print("Server started")
	
	def client_connect(self, conn):
		print(f"Client connected; Address: {conn.addr}; ID: {conn.id}")
	
	def client_disconnect(self, conn):
		print(f"Client disconnected; Address: {conn.addr}; ID: {conn.id}")

	def client_join_game(self, conn):
		print(f"Client joined game; Game ID: {conn.game.id}; Address: {conn.addr}; ID: {conn.id}")
	
	def client_leave_game(self, conn):
		print(f"Client left game; Game ID: {conn.game.id}; Address: {conn.addr}; ID: {conn.id}")
	
	def data_receive(self, conn):
		print(f"Data ready to be received; Client ID: {conn.id}")
	
	def game_create(self, game):
		print(f"Game created; ID: {game.id}; All game IDs: {game.server.getAllGameIds()}")
	
	def game_start(self, game):
		print(f"Game started; ID: {game.id}")
	
	def game_close(self, game):
		print(f"Game closed; ID: {game.id}; All game IDs: {game.server.getAllGameIds()}")

class Connection:
	def __init__(self, socket1, server):
		self.socket = socket1
		self.id = None
		self.addr = self.socket.getpeername()
		self.closed = False
		self.server = server
		self.game = None
	
	def joinGame(self):
		for game in self.server.games:
			if not game.started:
				self.game = game
				self.game.addPlayer(self)
				return
		
		newGame = self.server.gameClass(self.server)
		self.server.registerGame(newGame)
		self.game = newGame
		self.game.addPlayer(self)
	
	def send(self, data):
		self.socket.send(data)

	def close(self):
		if not self.closed:
			self.closed = True
			self.server.unregisterConn(self)
			self.socket.close()
			self.game.removePlayer(self)

	def fileno(self):
		return self.socket.fileno()

class Game:
	def __init__(self, server):
		self.id = None
		self.players = []
		self.started = False
		self.closed = False
		self.server = server
	
	def addPlayer(self, conn):
		if not self.started:
			self.players += [conn]
			self.server.eventHandler.client_join_game(conn)
			if len(self.players) == self.server.gameSize:
				self.started = True
				self.server.eventHandler.game_start(self) #run event
		else:
			raise Exception("player added to started game")
	
	def removePlayer(self, conn):
		self.players.remove(conn)
		self.server.eventHandler.client_leave_game(conn)
		if self.started or self.players == []:
			self.close()
	
	def sendAll(self, data, exceptFor=()):
		for player in self.players:
			if player not in exceptFor:
				player.send(data)
	
	def close(self):
		if not self.closed:
			self.closed = True
			for player in self.players:
				player.close()
			self.server.unregisterGame(self)

class NoData(Exception):
	pass

class Server:
	eventHandler = BaseEventHandler()
	connClass = Connection
	gameClass = Game
	
	def __init__(self, addr, gameSize):
		self.conns = []
		self.connIdCounter = 0
		self.games = []
		self.gameIdCounter = 0
		self.gameSize = gameSize
		self.closed = False
		
		self.socket = socket.socket()
		self.socket.setblocking(False)
		self.socket.bind(addr)
		
		self.selector = selectors.DefaultSelector()
		self.selector.register(self.socket, selectors.EVENT_READ, self.acceptConn)
	
	def start(self):
		self.eventHandler.server_start() #run event
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
	
	def setEventHandler(self, eventHandler):
		self.eventHandler = eventHandler
		return self
	
	def setConnClass(self, connClass):
		self.connClass = connClass
		return self
	
	def setGameClass(self, gameClass):
		self.gameClass = gameClass
		return self
	
	def acceptConn(self, socket1, mask):
		socket2, addr = socket1.accept()
		socket2.setblocking(False)
		
		conn = self.connClass(socket2, self)
		self.registerConn(conn)
		conn.joinGame()
	
	def readConn(self, conn, mask):
		try:
			self.eventHandler.data_receive(conn) #run event
		except (ConnectionResetError, NoData):
			conn.close()

	def registerConn(self, conn):
		conn.id = self.connIdCounter
		self.conns += [conn]
		self.connIdCounter += 1
		self.selector.register(conn, selectors.EVENT_READ, self.readConn)
		self.eventHandler.client_connect(conn) #run event
	
	def unregisterConn(self, conn):
		self.selector.unregister(conn)
		self.conns.remove(conn)
		self.eventHandler.client_disconnect(conn) #run event
	
	def registerGame(self, game):
		game.id = self.gameIdCounter
		self.games += [game]
		self.gameIdCounter += 1
		self.eventHandler.game_create(game) #run event
	
	def unregisterGame(self, game):
		self.games.remove(game)
		self.eventHandler.game_close(game) #run event
	
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
