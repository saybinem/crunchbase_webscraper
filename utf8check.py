import codecs
import os

os.system("chcp 65001")

for root, dirs, files in os.walk('./data/person/html'):
	files.sort()
	for file in files:
	
		filepath = os.path.join(root,file)
		print("Processing "+filepath)
		
		try:
			fileh = codecs.open(filepath, "r", "utf-8")
			cont = fileh.read()
			fileh.close()
		
		except UnicodeDecodeError:
			print("DECODE ERROR...continuing")
			exit()
