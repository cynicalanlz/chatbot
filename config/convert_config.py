with open("tapdone3.txt", 'r') as f:
	with open("tapdone3_supervisord.txt", 'w+') as o:
		parts = []
		for line in f.readlines():
			l = line.strip("\n").split("=")
			parts.append("{}='{}'".format(l[0], l[1]))
		o.write(','.join(parts))
