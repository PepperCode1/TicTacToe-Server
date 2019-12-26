#t3client

from t3data import packer
from dataUtils import NoDataReceivedException
import waitingIcon
import socket
import os, sys
import time

class Client:
	def __init__(self, addr):
		self.addr = addr
		self.sock = None
		self.curGame = None
	
	def printBoard(self):
		for i in range(self.curGame.boardSize*2-1):
			if i%2 == 0:
				print(str(self.curGame.board[i//2])[1:-1].replace(", ","│").replace("\'\'","   ").replace("\'"," "))
			else:
				print(self.curGame.separator)
	
	def getValidSpace(self):
		while True:
			try:
				space = eval(input("Enter row, column: "))
				if space[0] < 0 or space[1] < 0:
					print("Please enter a valid space.")
				else:
					if self.curGame.board[space[0]][space[1]] == "":
						return space
					else:
						print("That space is already taken.")
			except:
				print("Please enter a valid space.")
	
	def start(self):
		while True:
			self.sock = socket.socket()
			clearConsole()
			try:
				self.startGame()
			except ConnectionRefusedError: #no server
				print("Failed to connect to server")
			except ConnectionResetError: #server closed
				print("Server closed")
			except NoDataReceivedException: #connection closed
				print("Connection closed")
			
			again = input("Try again? (y/n) ").lower()
			if not(again == "y" or again == "yes"):
				break

	def startGame(self):
		self.curGame = Game(3)
		
		print("Connecting to server...")
		with waitingIcon.spinningBar1:
			self.sock.connect(self.addr) #connect to server
		print("Waiting for opponent...")
		with waitingIcon.spinningBar1:
			packer.recv(self.sock) #receive data id 0: start
		print("Game starting")

		header, data = packer.recv(self.sock) #receive data id 1
		symbol = str(data[0], "utf8")
		print("You are", symbol)
		time.sleep(2)

		while True:
			clearConsole()
			self.printBoard()
			if self.curGame.curPlayer == symbol:
				print("\nYour turn")
				space = self.getValidSpace() #get valid space from user
				self.curGame.board[space[0]][space[1]] = self.curGame.curPlayer #insert space into board
				
				packer.send(self.sock, (2,), space) #send sata id 2: space
			else:
				print("\nOpponent's turn")
				print("Waiting for opponent to make move...")
				
				with waitingIcon.spinningBar1:
					header, data = packer.recv(self.sock) #receive data id 2
				self.curGame.board[data[0]][data[1]] = self.curGame.curPlayer #insert space into board
			
			header, data = packer.recv(self.sock) #receive data id 4
			nextRound = data[0]
			if not nextRound:
				break
			
			self.curGame.swapPlayer()

		header, data = packer.recv(self.sock) #receive data id 5
		winPlayer = str(data[0], "utf8") #convert bytes to str
		clearConsole()
		if winPlayer == "X": #X wins
			print("X wins")
		elif winPlayer == "O": #O wins
			print("O wins")
		else: #tie
			print("Tie")

		print("\nFinal board:")
		self.printBoard()
		
		self.sock.close()

class Game:
	def __init__(self, boardSize):
		self.boardSize = boardSize
		self.board = [i.copy() for i in [[""]*boardSize]*boardSize]
		self.separator = "".join(("───" if i%2==0 else "┼") for i in range(boardSize*2-1))
		self.curPlayer = "X"
	
	def swapPlayer(self):
		self.curPlayer = "O" if self.curPlayer=="X" else "X"

def clearConsole():
	if sys.platform.startswith("linux"):
		clearCommand = "clear"
	else:
		clearCommand = "cls"
	os.system(clearCommand)

t3client = Client(("127.0.0.1", 5000))
#t3client = Client(("ec2-52-32-53-78.us-west-2.compute.amazonaws.com", 5000))
t3client.start()