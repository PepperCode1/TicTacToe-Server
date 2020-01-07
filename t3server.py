#t3server

from gameServer import *
from t3data import packer
from dataUtils import NoDataReceivedException
import random

class cEventHandler(BaseEventHandler):
	@staticmethod
	def on_data(conn):
		try:
			header, data = packer.recv(conn.socket)
		except NoDataReceivedException:
			raise NoData
		
		print(f"Data received; Client ID: {conn.id}; symbol: {conn.symbol}\n  Header: {header}\n  Data: {data}")
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
	
	@staticmethod
	def on_game_start(game):
		print(f"Game started; ID: {game.id}")
		
		game.customSetup(3)
		
		game.sendAll(packer.pack((0,), ())) #send data id 0: start
		if random.randint(0,1) == 0: #randomize player symbols
			game.players[0].customSetup("X")
			game.players[1].customSetup("O")
		else:
			game.players[0].customSetup("O")
			game.players[1].customSetup("X")
		
		for player in game.players: #send symbols
			packer.send(player.socket, (1,), (bytes(player.symbol,"utf8"),)) #send data id 1: symbol

class cConnection(Connection):
	def customSetup(self, symbol):
		self.symbol = symbol

class cGame(Game):
	def customSetup(self, boardSize):
		self.rounds = 0
		self.boardSize = boardSize
		self.board = [i.copy() for i in [[""]*self.boardSize]*self.boardSize]
		self.curPlayer = "X"
		self.prevPlayer = ""
	
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

def main():
	try:
		t3server = Server(("", 5000), 2)
		t3server.setEventHandlerClass(cEventHandler)
		t3server.setConnClass(cConnection)
		t3server.setGameClass(cGame)
	except:
		print("A server is already running on this address")
		return

	t3server.start()

if __name__ == "__main__":
	main()