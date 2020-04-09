import dataUtils

'''
Data IDs:
0 - start
1 - player symbol - X; O
2 - board space - [r][c]
3 - start next round - False; True
4 - game result - X; O; 0
'''

packer = dataUtils.DataPacker("H", "H")
packer.addDataStruct(0, "")
packer.addDataStruct(1, "c")
packer.addDataStruct(2, "HH")
packer.addDataStruct(3, "?")
packer.addDataStruct(4, "c")
