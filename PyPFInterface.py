import	os
import runpy
import	tkinter as tk
from	tkinter import ttk #ttk=themed tk
from	tkinter import messagebox
from	tkinter import filedialog

win	=	tk.Tk()
win.geometry("1400x800")
win.title("___Python Production Function Interface____")
win.option_add("*Font", "arial 9")

#status bar
#status = Label(win, text="processing…", bd=1, relief=SUNKEN, anchor=W) 
#status.pack(side=BOTTOM, fill=X)
import runpy
import pandas as pd

try:
	countryFile					='PyPF.country.parameters.default.csv'
	countryCreated			='PyPF.country.parameters.csv'
	CountryParams			=pd.read_csv(countryFile, header=0, index_col=2,keep_default_na=0,na_filter=0)
except:
	title		=	'Error'
	message		=	'The file PyPF.country.parameters.default.csv\n Must be exist in the current directory '
	messagebox.showinfo(title,message)
	win.destroy()
	exit()

try:
	generalFile				='PyPF.general.parameters.default.csv'
	generalCreated		='PyPF.general.parameters.csv'
except:
	title		=	'Error'
	message		=	'The file PyPF.general.parameters.default.csv\n Must be exist in the current directory '
	messagebox.showinfo(title,message)
	win.destroy()
	exit()
'''
try:
	tryopenfile	=	open('PyPF.xlsx','r+')
	tryopenfile.close()
except:
	title		=	'Error'
	message		=	'The file PyPF.xlsx is open\nPlease close your excel file '
	messagebox.showinfo(title,message)
'''
CountryParams_to		=pd.read_csv('PyPF.country.parameters_to.csv', header=0, index_col=2,keep_default_na=0,na_filter=0)

pays					=(CountryParams.loc[:,'at':'hr'])
pays_to				=(CountryParams_to.loc[:,'ALL'])


dicParamCountry			={}
dicParamCountry_to	={}

dicParamCountry			=pays.to_dict()
dicParamCountry_to	=pays_to.to_dict()

dicFrame			={}
rowG					=0
rFrameG			=tk.LabelFrame(win,text='PyPF results for YGAP',takefocus=True)

lstCode				='tfp_n','tfp_o','tfp_c','tfp_s','tfp_l','part_n','part_c','part_t','part_s','part_l','hpere_n','hpere_c','hpere_s','hpere_l','iypot_n','ypot_c','iypot_s','starthp'
lstFile				='amecoFile','tfpKFFile','nawruFile','popFile','MigrationFile','outFile'
dicCodeGenFromTo={'changey':('2020','2030','1'),'yf':('6','20','1'),'clos_nb_y':('3','10','1'),'OutputStartingYear':('1965','2020','1'),'alpha':('0.65','2.00','0.05')}

def readParamsFileCountry(inputFile):
	fileRead	=inputFile
	dicFile		={}
	file		=open(fileRead, 'r')
	for	record in file:
		row				=record.split(',')
		key 			=row[2].strip()#key = code
		dicFile[key]	=row[0].strip()+','+row[1].strip()+','+row[2].strip()
	file.close()
	return dicFile

def readParamsGeneral(inputFile):
	fileRead			=inputFile
	dicFileDefault	={}
	dicFileSelect	={}
	dicGenParam	={}
	file						=open(fileRead, 'r')
	metaGeneral	=file.readline() #1 record with meta
	for	record in file:
		row							=record.split(',')
		key 							=row[1].strip()#key = code
		dicGenParam[key]	=row[0].strip()+','+row[1].strip()+','
		if key in lstFile:
			dicFileSelect[key]		=''
			dicFileDefault[key]	=row[2].strip()
	file.close()
	return metaGeneral,dicFileDefault,dicFileSelect,dicGenParam

def	createParamsGeneral():
	fileOutputParamGeneral	=open(generalCreated, 'w')
	#fileInputParamGeneral	=open(generalFile, 'r')
	fileOutputParamGeneral.write('{}'.format(metaGeneral))
	for	code in	dicCodeGenSelect:
		valueCode	= dicCodeGenSelect[code].get()
		fileOutputParamGeneral.write('{}{}\n'.format(dicGenParam[code],valueCode))
	for	code in	dicFileDefault:
		if	len(dicFileSelect[code]) > 0:
			valueCode	= dicFileSelect[code]
		else:
			valueCode	= dicFileDefault[code]
		fileOutputParamGeneral.write('{}{}\n'.format(dicGenParam[code],valueCode))
	fileOutputParamGeneral.close()

def	createParamsCountry():
	dicFile		=	readParamsFileCountry(countryFile)
	fileOutputParamCountry	=open(countryCreated, 'w')
	#countries	=	dicFrame.keys()
	first_ctry	=	next(iter(dicFrame))
	codes		=	dicParamCountrySelect[first_ctry].keys()
	country		=	dicFile['code']
	for	c	in dicFrame:
		country		= country+ ','+ c
	fileOutputParamCountry.write('{}\n'.format(country))
	for	code in	codes:
		valueCode	= ''
		for c	in dicFrame:
			valueCode	= valueCode+','+dicParamCountrySelect[c][code].get()
		fileOutputParamCountry.write('{},{}\n'.format(dicFile[code],valueCode[1:]))
	fileOutputParamCountry.close()
	
def viewResultYGAP():
	try:
		tryopenfile	=	open('PyPF.xlsx','r+')
		tryopenfile.close()
	except:
		title		=	'Error'
		message		=	'The file PyPF.xlsx is open\nPlease close your excel file '
		messagebox.showinfo(title,message)
	global rowG, rFrameG
	#execute OutputGAP
	'''
	try:
		tryopenfile	=	open('PyPF.xlsx','r+')
		tryopenfile.close()
	except:#exit program, we cannot continue excel still open
		win.destroy()
		exit()
	'''
	#EXECUTE OUTPUTGAP
	outputGap	=runpy.run_path('PyPFv08.py')
	dicInterface={}
	dicInterface=outputGap['dicInterface']
	title		=	'PyPF is running'
	message		=	'Results are ready! '
	messagebox.showinfo(title,message)
	#
	rFrameG	=	tk.LabelFrame(win,text='PyPF Results for YGAP',takefocus=True,relief='solid')
	rFrameG.grid(column=0,row=rowG,sticky=tk.W)
	#rFrameG.columnconfigure(0,weight=0)
	col=1
	country_key	=	dicInterface.keys()
	first_ctry	=	next(iter(dicInterface))
	first_yyyy	=	next(iter(dicInterface[first_ctry]))
	yyyy_key	=	dicInterface[first_ctry][first_yyyy].keys()
	for c in dicInterface:
		cLabel	=ttk.Label(rFrameG, text=c, width=4)
		cLabel.grid(column=col, row=rowG, padx=4,sticky=tk.W)
		col+=1
	rowG+=1
	for yyyy in yyyy_key: 
		col=0
		cLabel	=ttk.Label(rFrameG, text=yyyy, width=6)#orig=4
		cLabel.grid(column=col, row=rowG,padx=3,sticky=tk.W)
		for country in country_key:
			col+=1
			code	=	country + '_Y_GAP(PF)'
			try:
				value	=	float("{:.1f}".format(dicInterface[country][code][yyyy]))
			except:
				value	= 	0.0
			cLabel	=ttk.Label(rFrameG, text=value, width=5)
			cLabel.grid(column=col, row=rowG,padx=2,sticky=tk.W)
		rowG+=1
	rFrameG.columnconfigure(0,weight=0)

def SelectAmeco():
	dicFileSelect['amecoFile']= filedialog.askopenfilename(initialdir='datafiles')
def SelectKalma():
	dicFileSelect['tfpKFFile']= filedialog.askopenfilename(initialdir='datafiles')
def SelectNawru():
	dicFileSelect['nawruFile']= filedialog.askopenfilename(initialdir='datafiles')
def SelectPop():
	dicFileSelect['popFile']= filedialog.askopenfilename(initialdir='datafiles')
def SelectPartDe():
	dicFileSelect['MigrationFile']= filedialog.askopenfilename(initialdir='datafiles')
def viewSelectFile():
	title	=	'Data files configuration'
	message	=	''
	selectFile	=	''
	for	code in	lstFile:
		if	dicFileSelect[code] != '':
			selectFile	= dicFileSelect[code]
		else:
			selectFile	= dicFileDefault[code]
		message	= message + code.strip() + '\t: ' + selectFile +"\n"
	messagebox.showinfo(title,message)
	
def RunGap():
	if	not dicFrame:
		title		=	'Error'
		message		=	'Sorry, you need to select at least one country before executing this option! '
		messagebox.showinfo(title,message)
		return
	global rowG, rFrameG
	try:
		rFrameG.destroy()
	except:
		pass
	#tk.Label(popup, text="OutputGap running").grid(row=0,column=0)
	#pb = ttk.Progressbar(popup, orient="horizontal", length=500, mode="determinate")
	#progress_bar = ttk.Progressbar(popup, variable=progress_var, maximum=100)
	#pb.start()
	#pb.grid(column=0,row=20)
	title	=	'PyPF is running with selection'
	message		=	'Please click OK and stay tuned...'
	messagebox.showinfo(title,message)
	createParamsGeneral()
	createParamsCountry()
	#execute OutputGAP
	viewResultYGAP()
	#pb.stop()
	
def RunGapDefault():
	import shutil
	global rowG, rFrameG
	try:
		rFrameG.destroy()
	except:
		pass
	title	=	'PyPF is running with default parameters'
	message		=	'Please click OK and stay tuned...'
	messagebox.showinfo(title,message)
	shutil.copy('PyPF.general.parameters.default.csv','PyPF.general.parameters.csv')
	shutil.copy('PyPF.country.parameters.default.csv','PyPF.country.parameters.csv')
	#
	viewResultYGAP()
	#pb.stop()

def RunExcel():
	os.system("start EXCEL.EXE PyPF.xlsx")

def About():
	title	=	'PyPF v0.8'
	message	=	'This program is a Python PILOT version of the program in ESTIMA RATS used by DG ECFIN to compute indicators needed for assessing both the productive capacity (i.e. potential output) and cyclical position (i.e. output gaps) of EU economies.\n\nPlease visit :\nhttps://github.com/ecfin-ygap/pypf\nfor updates!\n\nEngine : Francois BLONDEAU\nBodywork : Ramiro GOMEZ VILLALBA\nEuropean Commission, DG ECFIN'
	messagebox.showinfo(title,message)

def	commandCountry():
	col=1
	global rowG, rFrameG
	try:
		rFrameG.destroy()
	except:
		pass
	for c in dicCountry:
		if (dicCountry[c].get()):
			#create the frame if doesn't exist
			try:
				cFrame	=	dicFrame[c]
			except:
				cFrame	=	c+'Frame'
				cFrame	=	tk.Frame(win,takefocus=True)
				cFrame.bind('<FocusOut>',checkValue)
				cFrame.grid(column=0,row=rowG,sticky=tk.W)
				dicFrame[c]=cFrame
				col=0
				cLabel	=ttk.Label(cFrame, text=c, width=2)
				cLabel.grid(column=col, row=rowG,padx=4, sticky=tk.W)
				#print(dicParamCountry[c])
				for code in dicParamCountry[c]:
					col+=1
					dicParamCountrySelect[c][code]	=	tk.StringVar(value=dicParamCountrySelect[c][code].get())
					checkEntry=tk.Spinbox(cFrame,width=4,textvariable=dicParamCountrySelect[c][code],from_=dicParamCountry[c][code],to=dicParamCountry_to[code],takefocus=True)#,state='readonly')
					checkEntry.bind('<FocusOut>',checkValue)
					checkEntry.grid(column=col,row=rowG,padx=4,sticky=tk.E)
				(cFrame.winfo_children()[1]).focus()#focus on 1er element of the frame
		else:
			try:
				cFrame	=	dicFrame[c]
				cFrame.destroy()
				del dicFrame[c]
				(countryFrame.winfo_children()[0]).focus()#focus on 1er element of the country frame
			except:
				pass
		#win.update_idletasks()
		rowG+=1

def checkValue(evt):
	for c in dicFrame:
		for	code in dicParamCountrySelect[c]:
			try:
				setValue	=	int(dicParamCountrySelect[c][code].get())
			except:
				setValue	=	99999999
			if	setValue > dicParamCountry_to[code]:
				set			=	dicParamCountry_to[code]
				dicParamCountrySelect[c][code].set(set)
				title		=	code + '  FOR  ' + c
				message		=	'value must be between '+ str(dicParamCountry[c][code])+ ' and ' + str(dicParamCountry_to[code])
				messagebox.showinfo(title,message)
			if	setValue < dicParamCountry[c][code]:
				set			=	dicParamCountry[c][code]
				dicParamCountrySelect[c][code].set(set)
				title		=	code + '  FOR  ' + c
				message		=	'value must be between '+ str(dicParamCountry[c][code])+ ' and ' + str(dicParamCountry_to[code])
				messagebox.showinfo(title,message)
				
def checkValueGen(evt):
	for	code in dicCodeGenSelect:
		fromValue=float(dicCodeGenFromTo[code][0])
		toValue		=float(dicCodeGenFromTo[code][1])
		try:
			setValue	=	float(dicCodeGenSelect[code].get())
		except:
			setValue	=	9999999.0
		if	setValue > toValue:
			set			=	dicCodeGenFromTo[code][1]
			dicCodeGenSelect[code].set(set)
			title		=	code 
			message		=	'value must be between '+ str(dicCodeGenFromTo[code][0])+ ' and ' + str(dicCodeGenFromTo[code][1])
			messagebox.showinfo(title,message)
		if	setValue < fromValue:
			set			=	dicCodeGenFromTo[code][0]
			dicCodeGenSelect[code].set(set)
			title		=	code 
			message		=	'value must be between '+str(dicCodeGenFromTo[code][0])+ ' and ' + str(dicCodeGenFromTo[code][1])
			messagebox.showinfo(title,message)


dicCountry={}
dicParamCountrySelect={}
dicCheckCountry={}

metaGeneral,dicFileDefault,dicFileSelect,dicGenParam = readParamsGeneral(generalFile)
#define frame for general parameters
generalFrame=tk.LabelFrame(win,text='General parameters')
generalFrame.grid(column=0,row=rowG,sticky=tk.W)
rowG+=1
#define frame for list of countries
countryFrame=tk.LabelFrame(win,text='Country parameters')
countryFrame.grid(column=0,row=rowG,sticky=tk.W)
rowG+=1
#define frame for code of indicators
codeFrame=tk.LabelFrame(win,text='code of indicators',font="arial 10")
#codeFrame.option_add("*Font", "arial 10")
codeFrame.grid(column=0,row=rowG,padx=20,sticky=tk.W)

#frame for general parameters
dicCodeGenSelect={}
col=0
for	code in	dicCodeGenFromTo:
	cLabel	=ttk.Label(generalFrame, text=code)
	cLabel.grid(column=col,row=rowG,padx=2,sticky=tk.W)
	col+=1
	dicCodeGenSelect[code]	=	tk.StringVar(value=dicCodeGenFromTo[code][0])
	valueCode=dicCodeGenSelect[code]
	fromValue=dicCodeGenFromTo[code][0]
	toValue		=dicCodeGenFromTo[code][1]
	incValue	=dicCodeGenFromTo[code][2]
	spinEntry	=tk.Spinbox(generalFrame,width=4,textvariable=valueCode,from_=fromValue,to=toValue,increment=incValue,takefocus=True)#,state='readonly')
	spinEntry	.bind('<FocusOut>',checkValueGen)
	spinEntry.grid(column=col,row=rowG,padx=4,sticky=tk.E)
	col+=1
rowG+=1

#codeFrame.grid_propagate(0)
#create dict for country selection with default values
for c in dicParamCountry:
	for code in dicParamCountry[c]:
		try:
			dicParamCountrySelect[c][code]=tk.StringVar(value=dicParamCountry[c][code])
		except:
			dicParamCountrySelect[c]={}
			dicParamCountrySelect[c][code]=tk.StringVar(value=dicParamCountry[c][code])
#dicParamCountrySelect=dicParamCountry.copy()
#create frame with countries selection
col=0
for c in dicParamCountry:
	dicCountry[c]=tk.IntVar()
	dicCheckCountry[c]=tk.Checkbutton(countryFrame,text=c,variable=dicCountry[c],width=2,command=commandCountry)
	dicCheckCountry[c].grid(column=col,row=rowG,padx=1,sticky=tk.W)
	col+=1
	if	col == 14:
		col=0
		rowG+=1

#create code list in frame
col=1
rowG+=1
for	code in lstCode:
	cLabel	=ttk.Label(codeFrame, text=code, width=7)#orig=6
	cLabel.grid(column=col,row=rowG,padx=1,sticky=tk.E)#orig padx=2
	col+=1
rowG+=1
	
def startMenu():
	menu = tk.Menu(win)
	#menu.option_add("*Font", "arial 10")
	win.config(menu=menu)
	filemenu = tk.Menu(menu)
	menu.add_cascade(label="File", menu=filemenu)
	filemenu.add_command(label="Select amecoFile", command=SelectAmeco)
	filemenu.add_command(label="Select TFP KF data file", command=SelectKalma)
	filemenu.add_command(label="Select NAWRU data file", command=SelectNawru)
	filemenu.add_command(label="Select Population projetion data file (eurostat)", command=SelectPop)
	filemenu.add_command(label="Select migration file for DE", command=SelectPartDe)
	filemenu.add_separator()
	filemenu.add_command(label="View data files config", command=viewSelectFile)
	filemenu.add_command(label="Exit", command=win.quit)
	execute	= tk.Menu(menu)
	menu.add_cascade(label="Execute", menu=execute)
	execute.add_command(label="Run program with selected paramters", command=RunGap)
	execute.add_command(label="Run program with DEFAULT parameters", command=RunGapDefault)
	execute.add_command(label="Open result with excel", command=RunExcel)
	helpmenu = tk.Menu(menu)
	menu.add_cascade(label="Help", menu=helpmenu)
	helpmenu.add_command(label="About PyPF", command=About)

startMenu()
win.mainloop()
#win.resizable(0,0) #no frame resize


