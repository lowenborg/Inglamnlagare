# «Inglämnlagare» är ett program med öppen källkod. Den kan delas och redigeras utefter behov.
import os, re, sys, shutil, multiprocessing

def handlare(infil, utfil, omslag):
	sys.stdin = os.fdopen(utfil)
	print("\nUtfil:")
	while True:
		try:  # parallell metod för skyddad inmatning av sökväg till utfil, som körs på en egen processorkärna...
			utfil = input()  # ...medan bearbetningen redan sker i bakgrunden mot en tillfällig fil
			if os.path.dirname(os.path.abspath(utfil)) == os.getcwd():  # vid endast filnamn utan sökväg
				utfil = os.path.join(os.path.dirname(os.path.abspath(infil)), os.path.basename(utfil))
			if re.fullmatch(r"\s+|$", os.path.basename(utfil)) or re.search(r"(\\|\/)$", utfil):
				raise  # krav på något filnamn...
			if not utfil.endswith(".csv"):
				utfil = utfil + ".csv"  # ...men ej på filändelse
			if not os.path.exists(os.path.dirname(utfil)):
				os.makedirs(os.path.dirname(utfil))  # mappbildning vid behov
			if (os.path.basename(utfil)) in os.listdir(os.path.dirname(os.path.abspath(utfil))):
				raise  # koll om fil med samma namn redan finns
			oms = omslag.get()
			oms = utfil  # utskick av användarens inmatning tillbaka...
			omslag.put(oms)  # ...till moderprocessen i huvuddelen längst ner
			print("\n\nBearbetar...", end = "")
		except:
			omstart = "\rAnge full sökväg för utfil eller enbart dess namn för utskrift till infilens mapp:"
			if re.fullmatch(r"\s+|$", os.path.basename(utfil)) and not re.search(r"(\\|\/)$", utfil):
				print("\r", omstart)
			else:
				print("\n", omstart)
			continue
		else:
			break

def rensare(infil):
	rensning = os.path.join(os.path.dirname(os.path.abspath(infil)), "rensning")
	lagning = os.path.join(os.path.dirname(os.path.abspath(infil)), "lagning")
	
	with open(infil, "r", encoding = "UTF-8") as inf:
		with open(rensning, "w", encoding = "UTF-8") as ren:  # första bearbetningsmetoden; rensar nyrader samt skapar en ordlista av unika...
			for rad in inf:  # ...ensamstående spalter lamningtyp/egenskap och inbäddade fält lamningstyp/egenskap, som framtida spalter
				rad = re.sub(r"\n", r"", rad)
				rad = re.sub(r"(?<!,)(\"\d+\",)|(\d+\.?\d+,\d+\.?\d+,)(\"\d+\",)", r"\n\1\2\3", rad)
				ren.write(rad)  # återbildning av nyrad före varje fyndid, utan eller med koordinater
		
		with open(rensning, "r", encoding = "UTF-8") as ren:
			spalter = dict()
			for rad in ren:
				global kommatyp, kommaskap
				kommatyp = str("".join(re.findall(r".*,lamningtyp", rad)).count(","))
				kommaskap = str("".join(re.findall(r".*,egenskap", rad)).count(","))
				break
			for rad in ren:  # ensamstående spalter – urskiljare ↓↑ lägesräknare
				if kommatyp != "0":
					LT = "".join(re.findall(r"^(?:[^,]*?,){" + re.escape(kommatyp) + r"}(?!^)\"?(.*?)\"?,", re.sub(r",(?=[^\"]*\"[^\"]*(?:\"[^\"]*\"[^\"]*)*$)", r";", rad)))
					ES = "".join(re.findall(r"^(?:[^,]*?,){" + re.escape(kommaskap) + r"}(?!^)\"?(.*?)\"?,", re.sub(r",(?=[^\"]*\"[^\"]*(?:\"[^\"]*\"[^\"]*)*$)", r";", rad)))
					if ES == "": ES = "null"
					rad = re.sub(r"(^.*)", "\"[{\"\"lamningstyp\"\":\"\"" + re.escape(LT) + "\"\",\"\"antal\"\":1,\"\"egenskap\"\":\"\"" + re.escape(ES) + "\"\"}]\"" + r"\1", rad)
				rad = re.sub(r"(?<!\"\")null(?!\"\")", "\"\"null\"\"", rad)
				rad = re.sub(r"{\"\"lamningstyp\"\":\"\"([^\"]*)\"\",\"\"antal\"\":\d+,\"\"egenskap\"\":\"\"([^\"]*)\"\"}", r"«\1 – \2»", rad)
				rad = re.sub(r" – null|\\", r"", rad)
				rad = re.sub(r",", r";", rad)
				for typ in re.findall(r"(?<=«).*?(?=»)", rad):
					if typ not in spalter.values():  # insättningsordningsnummer – nyckel : lämningstypsegenskap – stoff
						spalter.update({len(spalter) + 1 : typ})
	
	lagare(rensning, lagning, spalter)

def lagare(rensning, lagning, spalter):
	with open(rensning, "r", encoding = "UTF-8") as ren:
		with open(lagning, "w", encoding = "UTF-8") as lag:
			for rad in ren:  # andra bearbetningsmetoden; skapar spalter utifrån ordlistan i föregående metod samt urskiljer, med reguttryck, antalen...
				rad = re.sub(r"(X,Y)?(,)?(fid,)(.*)", r"\3\4\2\1," + r",".join(spalter.values()), rad)  # ...vilka kopieras till sina platser i spalterna
				lag.write(rad)  # även flytt av eventuella koordinatspalter från längst TV till längst TH i tabellen
				break
		
		with open(lagning, "a", encoding = "UTF-8") as lag:
			for rad in ren:
				if kommatyp != "0":  # ensamstående spalter – urskiljare
					LT = "".join(re.findall(r"^(?:[^,]*?,){" + re.escape(kommatyp) + r"}(?!^)\"?(.*?)\"?,", re.sub(r",(?=[^\"]*\"[^\"]*(?:\"[^\"]*\"[^\"]*)*$)", r";", rad)))
					ES = "".join(re.findall(r"^(?:[^,]*?,){" + re.escape(kommaskap) + r"}(?!^)\"?(.*?)\"?,", re.sub(r",(?=[^\"]*\"[^\"]*(?:\"[^\"]*\"[^\"]*)*$)", r";", rad)))
					if ES == "": ES = "null"
				rad = re.sub(r"^(\d+\.?\d+,\d+\.?\d+)?(,)?(\"\d+\",)(.*)", r"\3\4\2\1", rad)
				if kommatyp != "0":
					led = re.sub(r"(^.*)", "\"[{\"\"lamningstyp\"\":\"\"" + re.escape(LT) + "\"\",\"\"antal\"\":1,\"\"egenskap\"\":\"\"" + re.escape(ES) + "\"\"}]\"" + r"\1", rad)
				else:
					led = rad
				led = re.sub(r"(?<!\"\")null(?!\"\")", "\"\"null\"\"", led)
				led = re.sub(r"{\"\"lamningstyp\"\":\"\"([^\"]*)\"\",\"\"antal\"\":(\d+),\"\"egenskap\"\":\"\"([^\"]*)\"\"}", r"«\1 – \3» \2", led)
				led = re.sub(r" – null|\\", r"", led)
				led = re.sub(r",", r";", led)
				samling = dict()  # en andra ordlista, för antalet fynd, med nycklar i form av nummer för respektive fynds...
				for fynd in re.findall(r"«.*?» \d+", led):  # ...lämningstyp och egenskap ur den första ordlistan
					nyckel = int([nummer for nummer, namn in spalter.items() if namn == "".join(re.findall(r"(?<=«).*?(?=»)", fynd))][0])
					stoff = int("".join(re.findall(r"\d+", fynd)))
					if nyckel not in samling:  # föregående ordlistas insättningsordningsnummer – nyckel : denna ordlistas fyndantal – stoff
						samling.update({nyckel : stoff})
					else:
						samling.update({nyckel : stoff + samling.get(nyckel)})
				samling = dict(sorted(samling.items()))
				ex = 0
				for nu in samling.keys():
					rad = re.sub(r"(^.*)", r"\1" + r"," * (nu - ex) + (str(samling.get(nu))), rad)
					ex = nu
				rad = re.sub(r"(^.*)", r"\1" + r"," * (len(spalter) - nu), rad)
				if not (kommatyp != "0" or re.findall(r"\"\"lamningstyp\"\"", rad)):
					rad = re.sub(r"(^.*)", r"\1" + r"," * len(spalter), rad)  # komman för tomma spalter
				lag.write(rad)
	
	os.remove(rensning)

if __name__ == "__main__":  # programmets huvud, med skydd för felaktigt infilsintag...
	multiprocessing.freeze_support()  # ...samt anrop till metoderna och hantering av utfil i slutfasen
	
	print("Inglämnlagare. Filip Antomonov; GIS, januari/november 2021.\n\n\nInfil:")
	while True:
		try:
			infil = input()  # skyddat intag av infil, med tillägg av sökväg vid endast filnamn...
			if os.path.dirname(os.path.abspath(infil)) == os.getcwd():
				if getattr(sys, "frozen", ""):  # ...till skriptets mapp (beroende på om det körs som ett program...
					infil = os.path.join(os.path.dirname(os.path.realpath(sys.executable)), os.path.basename(infil))
				else:  # ...eller som en källa)...
					infil = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.basename(infil))
			if not infil.endswith(".csv"):
				if (os.path.basename(infil) + ".csv") in os.listdir(os.path.dirname(os.path.abspath(infil))):
					infil = infil + ".csv"  # ...samt sökning av CSV-fil vid oangiven ändelse
				else:
					raise
		except:
			omstart = "\rAnge full sökväg för infil i CSV-format eller enbart dess namn för inläsning från skriptets mapp:"
			if re.fullmatch(r"\s+|$", os.path.basename(infil)) and not re.search(r"(\\|\/)$", infil):
				print("\r", omstart)
			else:
				print("\n", omstart)
			continue
		else:
			break
	
	omslag = multiprocessing.Queue()  # flerkärnigt anrop till metoden för utfilsinmatning...
	omslag.put(())  # ...användaren anger utfil medan bearbetningen redan har påbörjats i bakgrunden
	han = multiprocessing.Process(target = handlare, args = (infil, sys.stdin.fileno(), omslag))
	han.start()
	rensare(infil)
	han.join()
	utfil = omslag.get()
	shutil.move((os.path.join(os.path.dirname(os.path.abspath(infil)), "lagning")), (os.path.join(os.path.dirname(os.path.abspath(utfil)), "lagning")))
	os.rename((os.path.join(os.path.dirname(os.path.abspath(utfil)), "lagning")), (utfil))  # flytt och omdöpning av tempfil till det angivna utfilsläget
	print("\rKlar.       ", end = "")