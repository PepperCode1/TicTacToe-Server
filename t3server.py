#t3server

from gameServer import *
from t3data import packer
from dataUtils import NoDataReceivedException
import random

class cEventHandler(BaseEventHandler):
	def on_server_start():
		print("Server started")

	def on_client_connect(conn):
		print("Client connection; Address: %s; ID: %s; Game ID: %s" % (conn.addr, conn.id, conn.game.id))

	def on_client_disconnect(conn):
		print("Client disconnect; Address: %s; ID: %s; Game ID: %s" % (conn.addr, conn.id, conn.game.id))

	def on_data(conn):
		try:
			header, data = packer.recv(conn.socket)
		except NoDataReceivedException:
			raise NoData
		
		print("Data received; Client ID: %s; symbol: %s\n  Header: %s\n  Data: %s" % (conn.id, conn.symbol, header, data))
		dataId = header[0]
		if dataId == 2: #receive data id 2
			if conn.game.prevPlayer != conn.symbol and conn.game.checkSpace(*data): #checks: if different player and valid space
				conn.game.sendAll(packer.pack(header, data), exceptFor=(conn,)) #send data id 2: board space
				
				conn.game.curPlayer = conn.symbol
				conn.game.board[data[0]][data[1]] = conn.game.curPlayer #insert space into board
				conn.game.rounds += 1
				
				if conn.game.rounds >= conn.game.boardSize**2: #tie
					conn.game.sendAll(packer.pack((3,), (False,))) #send data id 4: no next round
					conn.game.sendAll(packer.pack((4,), (b"0",))) #send data id 5: tie
				else: #no tie
					win = conn.game.checkBoard(*data)
					if win: #win
						conn.game.sendAll(packer.pack((3,), (False,))) #send data id 4: no next round
						conn.game.sendAll(packer.pack((4,), (bytes(conn.symbol,"utf8"),))) #send data id 5: win
					else: #no win
						conn.game.sendAll(packer.pack((3,), (True,))) #send data id 4: start next round
				conn.game.prevPlayer = conn.game.curPlayer

	def on_game_create(game1):
		print("Game created; ID: %s; All game Ids: %s" % (game1.id, tuple(i.id for i in game1.server.games)))

	def on_game_start(game1):
		print("Game started; ID: %s" % game1.id)
		
		game1.boardSize = 3
		game1.board = [i.copy() for i in [[""]*game1.boardSize]*game1.boardSize]
		
		game1.sendAll(packer.pack((0,), ())) #send data id 0: start
		if random.randint(0,1) == 0: #randomize player symbols
			game1.players[0].symbol = "X"
			game1.players[1].symbol = "O"
		else:
			game1.players[0].symbol = "O"
			game1.players[1].symbol = "X"
		
		for player in game1.players: #send symbols
			packer.send(player.socket, (1,), (bytes(player.symbol,"utf8"),)) #send data id 1: symbol

	def on_game_close(game1):
		print("Game closed; ID: %s; All game Ids: %s" % (game1.id, tuple(i.id for i in game1.server.games)))

class cConnection(Connection):
	symbol = None #set later

class cGame(Game):
	rounds = 0
	boardSize = None #set later
	board = None #set later
	curPlayer = "X"
	prevPlayer = ""
	
	def checkSpace(self, r, c):
		try:
			if r < 0 or c < 0:
				return False
			else:
				return self.board[r][c] == ""
		except:
			return False
	
	def checkBoard(self, r, c):
		counters = [0,0,0,0] #row,column,diagonaltopleft,diagonaltopright
		for i in range(self.boardSize):
			symbols = [self.board[r][i], self.board[i][c], self.board[i][i], self.board[i][self.boardSize-i-1]]
			for j in range(len(symbols)):
				if symbols[j] == self.curPlayer:
					counters[j] += 1
		return self.boardSize in counters

try:
	t3server = Server(("", 5000), 2)
	t3server.setEventHandlerClass(cEventHandler)
	t3server.setConnClass(cConnection)
	t3server.setGameClass(cGame)
except:
	print("A server is already running on this address")
	exit()

t3server.start()