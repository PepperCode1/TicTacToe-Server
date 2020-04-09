#t3server

from gameServer import Server, BaseEventHandler, Connection, Game, NoData
from t3data import packer
from dataUtils import NoDataReceivedException
import random

class CEventHandler(BaseEventHandler):
	def data_receive(self, conn):
		try:
			header, data = packer.recv(conn.socket)
		except NoDataReceivedException:
			raise NoData
		
		print(f"Data received; Client ID: {conn.id}; Symbol: {conn.symbol}\n  Header: {header}\n  Data: {data}")

		game = conn.game
		dataId = header[0]
		if dataId == 2: #receive data id 2
			if game.prevPlayer != conn.symbol and game.checkSpace(*data): #if different player and valid space
				game.sendAll(packer.pack(header, data), exceptFor=(conn,)) #send data id 2: board space
				
				game.curPlayer = conn.symbol
				game.board[data[0]][data[1]] = game.curPlayer #insert space into board
				game.rounds += 1
				
				win = game.checkBoard(*data)
				if win: #win
					game.sendAll(packer.pack((3,), (False,))) #send data id 3: no next round
					game.sendAll(packer.pack((4,), (bytes(conn.symbol,"utf8"),))) #send data id 4: win
				else: #no win
					if game.rounds >= game.boardSize**2: #tie
						game.sendAll(packer.pack((3,), (False,))) #send data id 3: no next round
						game.sendAll(packer.pack((4,), (b"0",))) #send data id 4: tie
					else: #no tie
						game.sendAll(packer.pack((3,), (True,))) #send data id 3: start next round
						
				game.prevPlayer = game.curPlayer
	
	def game_start(self, game):
		print(f"Game started; ID: {game.id}")
		
		game.setup(3)
		
		game.sendAll(packer.pack((0,))) #send data id 0: start
		if random.randint(0, 1) == 0: #randomize player symbols
			game.players[0].setup("X")
			game.players[1].setup("O")
		else:
			game.players[0].setup("O")
			game.players[1].setup("X")
		
		for player in game.players: #send symbols
			packer.send(player.socket, (1,), (bytes(player.symbol,"utf8"),)) #send data id 1: symbol

class CConnection(Connection):
	def setup(self, symbol):
		self.symbol = symbol

class CGame(Game):
	def setup(self, boardSize):
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

		t3server.setEventHandler(CEventHandler())
		t3server.setConnClass(CConnection)
		t3server.setGameClass(CGame)
	except:
		print("A server is already running on this address")
		return

	t3server.start()

if __name__ == "__main__":
	main()
