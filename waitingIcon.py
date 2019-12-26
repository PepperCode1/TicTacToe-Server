import threading
import time

class WaitingIcon:
	def __init__(self, icons, delay):
		self.icons = icons
		self.delay = delay
		self.animated = False

	def start(self):
		self.thread = threading.Thread(target=self.animate)
		self.thread.start()

	def stop(self):
		self.animated = False

	def __enter__(self):
		self.start()

	def __exit__(self, type1, value, traceback):
		self.stop()
		self.thread.join()

	def animate(self):
		self.animated = True
		icon = self.iconGen()
		while self.animated:
			print("\r"+next(icon), end="")
			time.sleep(self.delay)
		print("\r",end="")

	def iconGen(self):
		while True:
			for icon in self.icons:
				yield icon

spinningBar = WaitingIcon(["|","/","-","\\"], 0.1)
spinningBar1 = WaitingIcon(["│","╱","─","╲"], 0.1)