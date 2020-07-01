from vharfbuzz import Vharfbuzz
import sys

font1 = Vharfbuzz(sys.argv[1])
font2 = Vharfbuzz(sys.argv[2])

text = sys.argv[3]

history1 = []
history2 = []
def onchange1(font, stage, lookupid, buf):
	global history1
	history1.append((stage,lookupid, buf))
def onchange2(font, stage, lookupid, buf):
	global history2
	history2.append((stage,lookupid, buf))

def poskey(pos):
	skey = ""
	if pos[0] != 0 or pos[1] != 0:
		skey = "<%i,%i>" % (pos[0],pos[1])
	if pos[2] != 0:
		skey = skey + ("+%i" % pos[2])
	return skey

def key(buf):
	return "|".join(["%s=%i%s" % (b[0],b[1], poskey(b[2])) for b in buf])

font1.shape(text, onchange=onchange1)
font2.shape(text, onchange=onchange2)
for h in history1: print(h)
print("")
for h in history2: print(h)
if history1[-1] != history2[-1]:
	for h1, h2 in zip(history1, history2):
		if h1[2] == h2[2]:
			print("%s(%2i/%2i)\t%s" % (h1[0], h1[1], h2[1], key(h1[2])))
		else:
			print("First difference appeared at lookup %i (font1) %i (font2)" % (h1[1],h2[1]))
			print("font1\t\t%s " % key(h1[2]))
			print("font2\t\t%s " % key(h2[2]))
			break