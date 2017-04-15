#!/usr/bin/python
import os, time, datetime
import sys
import logging
from logging.handlers import SysLogHandler
from logging.handlers import TimedRotatingFileHandler


data = {}
items = []

for arg in sys.argv:
        if arg.find('=') >0 :
                strArg=arg.split('=')
                data[strArg[0]]=strArg[1]

loadDataResult=data['infile']+".tmp"

#### application error handler
loggerapp = logging.getLogger('swifttps')
handlerapp = TimedRotatingFileHandler('./logs/application.log', when="d", interval=1, backupCount=30)
loggerapp.addHandler(handlerapp)

def sendLogApp(msg) :
    loggerapp.error(msg)

def funcExecuteCommand(cmd) :
        result=commands.getstatusoutput(cmd)
        return result[1]

def fileLineRead(fileName):
        f=open(fileName)
        fw=open(fileName+".bak","w")
        while 1:
                line = f.readline()
                if not line:
                        break
                fw.write(line.split(' ')[0]+ ' ' + line.split(' ')[1] + ' ' +str(dataRead(line.split(' ')))+' dummy\n')
        f.close()
        fw.close()

def dataRead(data):
        startDate = datetime.datetime.now() - datetime.timedelta(minutes=1)
        startPoint=long(data[2])

	filename=data[0]+ "/" +startDate.strftime("%Y%m") +"/" +startDate.strftime("%d") +"/" +data[1] +"-"+startDate.strftime("%Y%m%d%H")
	print filename
	if not os.path.exists(filename):
		return startPoint
	else:
        	f1=open(filename)

        f2=open(loadDataResult,'a+')
        lineno = 0

        for line in f1:
                lineno += 1
                if lineno > startPoint:
                        f2.write(line)
        endPoint=lineno
	print endPoint

        f1.seek(1)
        if startPoint > endPoint:
                startPoint=0
                for line in f1:
                        f2.write(line)


        lines = endPoint-startPoint
        #print lines
        #print startPoint

        f1.close()
        f2.close()
        return endPoint

def fileProcess(fileName):
        startDate = datetime.datetime.now() - datetime.timedelta(minutes=1)
        f=open(fileName)
        bkfile=open(data['outfile']+"-backuptarget-"+startDate.strftime("%Y%m%d%H%M"),"a+b")

        while 1:
                line = f.readline()
                if not line:
                        break

                if len(line.split()) < 17 or line.find("ERROR with Object server") > 0 or line.find("Handoff requested") > 0 :
                        continue
		if not ( line.find(" GET ") > 0 or line.find(" PUT ") or line.find(" DELETE ") or line.find(" HEAD ") or line.find(" COPY ") ) :
			continue
                try :
                        strLine = line.split()
                        strHost = strLine[4]
                        strMethod = strLine[8]
                        strUri = strLine[9]
                        strCode = strLine[11]
                        strByte = strLine[15]
                        strByteRecv = strLine[16]
                        strResptime = strLine[20]
                        arrUri=strUri.split('/')

                        # backup
                        if (strMethod == "PUT" or strMethod == "DELETE") and strCode.startswith("20") :
                                if line.find("X-Sds-Backup:") < 0 :
                                        bkfile.write(strUri + " " + strMethod + " " + strCode + " \n")

                        if len(arrUri) == 4 :
                                strMethod = strMethod + "Container"
                        elif len(arrUri) == 3 :
                                strMethod = strMethod + "Account"
                        elif len(arrUri) > 4 :
                                strMethod = strMethod + "Object"
                        strTenant = arrUri[2].split('%3F')[0]
                except :
			sendLogApp(line)
                        pass

                try :

                        if strByte=="-" and strByteRecv!="-" :
                                strByte=strByteRecv
                        if strByte=="-" :
                                strByte=0

                        if data.get('Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode + ' Bytes') :
                                data['Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode + ' Bytes'] += long(strByte)
                        else :
                                data['Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode + ' Bytes'] = long(strByte)


                        if data.get('Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode + ' Resptime') :
                                data['Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode + ' Resptime'] += float(strResptime)
                        else :
                                data['Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode + ' Resptime'] = float(strResptime)

                        if data.get('Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode) :
                                data['Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode] += 1
                        else :
                                data['Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode] = 1
                                items.append('Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode)
                                data['Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode + ' Resp_5'] = 0
                                data['Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode + ' Resp1'] = 0
                                data['Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode + ' Resp2'] = 0
                                data['Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode + ' Resp2o'] = 0

                                data['Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode + ' Size1'] = 0
                                data['Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode + ' Size2'] = 0
                                data['Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode + ' Size3'] = 0
                                data['Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode + ' Size4'] = 0
                                data['Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode + ' Size5'] = 0

                        if float(strResptime) <= 0.33 :
                                data['Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode + ' Resp_5'] += 1
                        elif float(strResptime) <= 1.0 :
                                data['Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode + ' Resp1'] += 1
                        elif float(strResptime) <= 2.0 :
                                data['Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode + ' Resp2'] += 1
                        elif float(strResptime) > 2.0 :
                                data['Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode + ' Resp2o'] += 1

                        if long(strByte) <= 300000 :
                                data['Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode + ' Size1'] += 1
                        elif long(strByte) <= 1000000 :
                                data['Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode + ' Size2'] += 1
                        elif long(strByte) <= 2000000 :
                                data['Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode + ' Size3'] += 1
                        elif long(strByte) <= 5000000 :
                                data['Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode + ' Size4'] += 1
                        elif long(strByte) > 5000000 :
                                data['Tenant='+ strTenant + ' Method=' + strMethod + ' Code=' + strCode + ' Size5'] += 1

                except :
			sendLogApp(line)
                        print line
                        print "Unexpected error:", sys.exc_info()[0]
                        pass

        f.close()
        bkfile.close()

        fw=open(data['outfile']+'-accesslog-'+startDate.strftime("%Y%m%d"),"a+b")
        for item in items :
                fw.write("Host=" + data['host'])
                fw.write(" " +item)
                fw.write(" Count=" + str(data[item]))
                fw.write(" Bytes=" + str(data[item + ' Bytes']))
                fw.write(" Resptime=" + str(data[item + ' Resptime']) + " avg_Bytes=" + str(data[item + ' Bytes']/data[item]))
                fw.write(" avg_Resptime=" + str(data[item + ' Resptime']/data[item]))
                fw.write(" Resptime_5=" + str(data[item + ' Resp_5']))
                fw.write(" Resptime1=" + str(data[item + ' Resp1']))
                fw.write(" Resptime2=" + str(data[item + ' Resp2']))
                fw.write(" Resptime2over=" + str(data[item + ' Resp2o']))
                fw.write(" TPS=" + str( float(data[item])/float(data['interval']) ) )
                fw.write(" swift=" + str(data['swift']))
                fw.write("\n")

                fw.write("Host=" + data['host'])
                fw.write(" " +item)
#                fw.write(" Count=" + str(data[item]))
#                fw.write(" Bytes=" + str(data[item + ' Bytes']))
#                fw.write(" Resptime=" + str(data[item + ' Resptime']) + " avg_Bytes=" + str(data[item + ' Bytes']/data[item]))
#                fw.write(" avg_Resptime=" + str(data[item + ' Resptime']/data[item]))
                fw.write(" Size1=" + str(data[item + ' Size1']))
                fw.write(" Size2=" + str(data[item + ' Size2']))
                fw.write(" Size3=" + str(data[item + ' Size3']))
                fw.write(" Size4=" + str(data[item + ' Size4']))
                fw.write(" Size5=" + str(data[item + ' Size5']))
                fw.write(" swift=" + str(data['swift']))
                fw.write("\n")

        fw.close()

fileLineRead(data['infile'])
os.rename (data['infile']+".bak",data['infile'])

fileProcess(loadDataResult)
os.remove (loadDataResult)
