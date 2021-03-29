#!/usr/bin/env python3

#autor: Jakub Komarek
#login: xkomar33
#ipp- interperet kodu v xml
import sys
import os
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
import re
import collections

def main():
    INPUT,SOURCE=parametersParse(sys.argv)      #zpracování parametrů
    tree=xmlTreeParsing(SOURCE)                 #získání ze xml stromovou strukturu
    root=tree.getroot()                         
    MyProgram=programParsing(root)              #zpracování xml stromu 
    MyProgram.setInput(INPUT)
    MyProgram.firstRun()                        #první průchod programem-kontrola operátárů a jejich parametů(hlavně syntaktické kontroly), zaznammání pozic skoků
    MyProgram.secondRun()                      #druhý průchod programem-samotné provedení instrukcí
    exit(0)
class Instrucrion(object):
    Type=""
    args={}
    def __init__(self,op,args):
        op=op.upper()
        self.args=args
        if(op=="RETURN"or op=="CREATEFRAME"or op=="PUSHFRAME"or op=="POPFRAME"or op=="BREAK"):
            self.paramCheck()
        elif(op=="ADD"or op=="SUB"or op=="MUL"or op=="IDIV"or op=="LT"or op=="GT"or op=="EQ"or op=="AND"or op=="OR"or op=="STRI2INT"or op=="CONCAT"or op=="GETCHAR"or op=="SETCHAR"):
            self.paramCheck("var","sym","sym")
        elif(op=="MOVE" or op=="NOT"):
            self.paramCheck("var","sym")
        elif(op=="INT2CHAR"or op=="STRLEN"or op=="TYPE"):
            self.paramCheck("sym","sym")
        elif(op=="DEFVAR"or op=="POPS"):
            self.paramCheck("var")
        elif(op=="JUMPIFEQ"or op=="JUMPIFNEQ"):
            self.paramCheck("label","sym","sym")
        elif(op=="LABEL"or op=="CALL"or op=="JUMP"):
            self.paramCheck("label")
        elif(op=="PUSHS"or op=="WRITE"or op=="EXIT"or op=="DPRINT"):
            self.paramCheck("sym")
        elif(op=="READ"):
            self.paramCheck("var","type")
        else:
            error(32,"Unknown op Code")     
        self.Type=op
    def __repr__(self):
        return "<Instruction - type: %s,\t args:%s >\n" % (self.Type, self.args)
    def paramCheck(self,*args):     #porovnání typů parametrů instrukcí s očekávanými typy
        if(len(args)!=len(self.args)):
            error(32,"to few or to much paremeters on instruction")
        paramCounter=0
        for arg in args:
            paramCounter+=1
            if(not(str(paramCounter) in self.args)):
                error(32,"parameter not found")
            Type=self.args[str(paramCounter)].Type
            if(arg=="sym"):
                if(not(Type=="bool" or Type=="var" or Type=="string" or Type=="int" or Type=="nil")):
                    error(32,"arg check error")
            elif(Type!=arg):
                error(32,"arg check error")
class operant(object):
    Type=""
    value=""
    placement=None
    def __init__(self,Type,value):
        self.Type=Type
        if(self.Type=="var"):
            separated=value.split('@',1)
            if((separated[0]=="GF" or separated[0]=="LF" or separated[0]=="TF")and (separated[1]!="")):
                if not re.match(r"^[A-Za-z_\-$&%;*!?][A-Za-z0-9_\-$&%;*!?]*$", separated[1]):
                    error(32,"variable name invalid")
                value=separated[1]
                self.placement=separated[0]
            else:    
                error(32,"Varieble format not valid")     
        elif(self.Type=="bool"):
            if(value=="true"):
                value=True
            elif(value=="false"):
                value=False
            else:
                error(32,"Bool value not valid")
        elif(self.Type=="int"):
            if(re.match(r"^((\+|\-)?(0|[1-9][0-9]*))$", value)):
                try:
                    value=int(value)
                except ValueError:
                    error(32,"Int coverzion error after regex checks")
            else:
                error(32,"INT value not valid")
        elif(self.Type=="string"):
            if value==None:
                value=""
            else:
                value=stringConverter(value)
        elif(self.Type=="nil" and value=="nil"):
            value=None
        elif(self.Type=="type"):
            if(not re.match(r"^(nil|bool|int|string)$", value)):
                error(32,"Type invalid")
        elif(self.Type=="label"):
            if(not re.match(r"^([A-Za-z_\-$&;%*!?][A-Za-z0-9_\-$&%;*!?]*)$", value)):
                error(32,"Label value not valid")
        else:   
            error(32,"unknown type")
        self.value=value
    def __repr__(self):
        return "<Operant - type: %s, value: %s ,placement: %s>" % (self.Type, self.value, self.placement)
class jumpTable(object):   
    table={}
    callStack=[]
    def __init__(self):
        self.table={}
        callStack=[]
    def addJump(self,name,colum):
        if(name in self.table):
            error(32,"duplicit label")
        else:
            self.table[name]=colum
class frame(object):
    varS={}
    def __init__(self):
        self.varS={}
class notInicializet:
    def __init__(self):
        pass
    def __str__(self):
        return "not inicializet"
    def __repr__(self):
        return "var not inicializet"
class memory(object):
    GF=frame()
    TF=None
    LF=None
    stack=[]
    varStack=[]
    def writeToVAR(self,arg,Value):
        frameType=arg.placement
        name=arg.value
        if frameType=="GF":
            if not name in self.GF.varS:
                error(54,"Moving destination doesnt exist in GF")
            self.GF.varS[name]=Value
        elif frameType=="LF":
            if self.LF==None:
                error(55,"LF Frame dont exist")
            elif not name in self.stack[-1].varS:
                error(54,"Moving destination doesnt exist in LF")
            self.LF.varS[name]=Value
        elif frameType=="TF":
            if self.TF==None:
                error(55,"TF Frame dont exist")
            elif not name in self.TF.varS:
                error(54,"Moving destination doesnt exist in TF")
            self.TF.varS[name]=Value
        else:
            error(99,"this frame type dont exists")
    def readFromVar(self,arg,forType=False):
        Value=None
        name=arg.value
        frameType=arg.placement
        if frameType=="GF":
            if not name in self.GF.varS:
                error(54,"Var  doesnt exist in GF")
            Value=self.GF.varS[name]
        elif frameType=="LF":
            if self.LF==None:
                error(55,"LF Frame dont exist")
            elif not name in self.stack[-1].varS:
                error(54,"Var destination doesnt exist in LF")
            Value=self.LF.varS[name]
        elif frameType=="TF":
            if self.TF==None:
                error(55,"TF Frame dont exist")
            elif not name in self.TF.varS:
                error(54,"Var destination doesnt exist in TF")
            Value=self.TF.varS[name]
        else:
            error(99,"this frame type dont exists")
        if (type(Value)==notInicializet) and not forType:
            error(56,"Reading from uninicializet var")
        return Value
    def CREATEFRAME(self):
        self.TF=frame()
    def PUSHFRAME(self):
        if(self.TF==None):
            error(55,"pushing tf frame that not exist")
        self.stack.append(self.TF)
        self.LF=self.stack[-1]
        self.TF=None
    def POPFRAME(self):
        if(not self.stack):
            error(55,"cant pop from empty stack")
        self.TF=self.stack.pop(-1) 
        if(self.stack):
            self.LF=self.stack[-1]
        else:
            self.LF=None
    def DEFVAR(self,args):
        var=args["1"]
        if var.placement=="GF":
            if var.value in self.GF.varS:
                error(52,"Defvar err-duplicit name of var in GF")
            self.GF.varS[var.value]=notInicializet()
        elif var.placement=="LF":
            if self.LF==None:
                error(55,"LF Frame dont exist")
            elif var.value in self.stack[-1].varS:
                error(52,"Defvar err-duplicit name of var in LF")
            self.stack[-1].varS[var.value]=notInicializet()
        elif var.placement=="TF":
            if self.TF==None:
                error(55,"TF Frame dont exist")
            elif var.value in self.TF.varS:
                error(52,"Defvar err-duplicit name of var in TF")
            self.TF.varS[var.value]=notInicializet()
        else:
            error(99,"defvar err")
    def MOVE(self,args):
        self.writeToVAR(args["1"],args["2"].value)
    def __repr__(self):
        GF=frame()
        TF=None
        LF=None
        if(self.TF!=None):
            TF=self.TF.varS
        if(self.LF!=None):
            LF=self.LF.varS
        return "<Mem - GF:\n %s  \nLF:\n %s \nTF:\n %s \nstack:\n%s>\n" % (self.GF.varS,LF, TF,self.stack)
class program(object):   
    instructructions=[]
    jTable=jumpTable()
    mem=memory()
    counter=0
    procesedInstruct=0
    inputSource=None
    inputFile=None
    inputFileErr=False
    def __init__(self,instructructions):
        self.instructructions=instructructions
        self.jTable=jumpTable()
        self.mem=memory()
        self.counter=0
        self.procesedInstruct=0
    def setInput(self,InputS):
        self.inputSource=InputS
    def openFile(self):
        try:
            self.inputFile=open(self.inputSource,"r")
        except:
            inputFileErr=True
    def __repr__(self):
        return "<Program: - instructions:\n %s \nJumptable:\n %s" % (self.instructructions,self.jTable)    
    def firstRun(self):
        for i in range(0, len(self.instructructions)):
            if(self.instructructions[i].Type=="LABEL"):
                name=self.instructructions[i].args["1"].value
                if(name in self.jTable.table):
                    error(52,"duplicit label")
                else:
                    self.jTable.table[name]=i
    def secondRun(self):
        while self.counter<len(self.instructructions):
            self.procesedInstruct+=1
            self.execute(self.instructructions[self.counter])
            self.counter+=1
    def execute(self,instruction):
        if instruction.Type=="MOVE":
            self.mem.MOVE(instruction.args)
        elif instruction.Type=="CREATEFRAME":
            self.mem.CREATEFRAME()
        elif instruction.Type=="PUSHFRAME":
            self.mem.PUSHFRAME()
        elif instruction.Type=="POPFRAME":
            self.mem.POPFRAME()
        elif instruction.Type=="DEFVAR":
            self.mem.DEFVAR(instruction.args)
        elif instruction.Type=="CALL":
            self.CALL(instruction.args)
        elif instruction.Type=="RETURN":
            self.RETURN()
        elif instruction.Type=="PUSHS":
            self.PUSHS(instruction.args)
        elif instruction.Type=="POPS":
            self.POPS(instruction.args)
        elif instruction.Type=="ADD":
            self.ARITMETIC(instruction.args,"ADD")
        elif instruction.Type=="SUB":
            self.ARITMETIC(instruction.args,"SUB")
        elif instruction.Type=="MUL":
            self.ARITMETIC(instruction.args,"MUL")
        elif instruction.Type=="IDIV":
            self.ARITMETIC(instruction.args,"IDIV")
        elif instruction.Type=="LT":
            self.COMPARISON(instruction.args,"LT")
        elif instruction.Type=="GT":
            self.COMPARISON(instruction.args,"GT")
        elif instruction.Type=="EQ":
            self.COMPARISON(instruction.args,"EQ")
        elif instruction.Type=="AND":
            self.BINARY(instruction.args,"AND")
        elif instruction.Type=="OR":
            self.BINARY(instruction.args,"OR")
        elif instruction.Type=="NOT":
            self.BINARY(instruction.args,"NOT")
        elif instruction.Type=="INT2CHAR":
            self.INT2CHAR(instruction.args)
        elif instruction.Type=="STRI2INT":
            self.STRI2INT(instruction.args)
        elif instruction.Type=="READ":
            self.READ(instruction.args)
        elif instruction.Type=="WRITE":
            self.WRITE(instruction.args,False)
        elif instruction.Type=="CONCAT":
            self.CONCAT(instruction.args)
        elif instruction.Type=="STRLEN":
            self.STRLEN(instruction.args)
        elif instruction.Type=="GETCHAR":
            self.GETCHAR(instruction.args)
        elif instruction.Type=="SETCHAR":
            self.SETCHAR(instruction.args)
        elif instruction.Type=="TYPE":
            self.TYPE(instruction.args)
        elif instruction.Type=="LABEL":
            pass
        elif instruction.Type=="JUMP":
            self.JUMP(instruction.args)
        elif instruction.Type=="JUMPIFEQ":
            self.JUMPIFEQ(instruction.args)
        elif instruction.Type=="JUMPIFNEQ":
            self.JUMPIFNEQ(instruction.args)
        elif instruction.Type=="EXIT":
            self.EXIT(instruction.args)
        elif instruction.Type=="DPRINT":
            self.WRITE(instruction.args,True)
        elif instruction.Type=="BREAK":
            self.BREAK()
        else:
            error(99,"unknow procedure for instruction execution")
    def WRITE(self,args,debug):
        if(args["1"].Type=="var"):
            value=self.mem.readFromVar(args["1"])
            if type(value)==bool:
                if(value==True):
                    value="true"
                else:
                    value="false"
            elif type(value)==str or type(value)==int:
                pass
            else:
                return
        else:
            if args["1"].Type=="bool":
                if(args["1"].value==True):
                    value="true"
                else:
                    value="false"
            elif args["1"].Type=="string" or args["1"].Type=="int":
                value=args["1"].value
            else:
                return
        if debug:
            print(value,end ="", file=sys.stderr) 
        else:
            print(value, end ="")
    def CALL(self,args):
        self.jTable.callStack.append((self.counter))
        self.JUMP(args)
    def RETURN(self):
        if(self.jTable.callStack):
            self.counter=self.jTable.callStack[-1]
            self.jTable.callStack.pop(-1)
        else:
            error(56,"return stack is empty")
    def JUMP(self,args):
        if args["1"].value in self.jTable.table:
            self.counter=self.jTable.table[args["1"].value]
        else:
            error(52,"Jump label isnt in code")
        pass
    def JUMPIFEQ(self,args):
        a=self.loadValue(args["2"])
        b=self.loadValue(args["3"])
        if(type(a)==None) or (type(b)==None):
            error(53,"JUMPIFEQ err- nil value in params is permited")
        if type(a)==type(b) and a==b:
            self.JUMP(args)
    def JUMPIFNEQ(self,args):
        a=self.loadValue(args["2"])
        b=self.loadValue(args["3"])
        if(type(a)!=type(b) or type(a)==None):
            error(53,"JUMPIFEQ err- nil value in params is permited")
        if a!=b:
            self.JUMP(args)     
    def DPRINT(self,args):
        error(0,str(self.loadValue(args["1"])))
    def BREAK(self):
        error(0,"================================================\nDebug write\nPozition in code: %d\nCount of executed instructions: %d\nVAR stack:%s\nMemory:\n%s================================================"% (self.counter,self.procesedInstruct,self.mem.varStack,self.mem))
    def EXIT(self,args):
        retCode=-1
        try:
            retCode=int(self.loadValue(args["1"]))
        except  ValueError:
            exit(53)
        except  TypeError:
            exit(53)
        if retCode <0 or retCode>49:
            exit(57)
        exit(retCode)
    def loadValue(self,arg,forType=False):
        if arg.Type=="var":
            value=self.mem.readFromVar(arg,forType)
        else:
            value=arg.value
        return value
    def PUSHS(self,args):
        self.mem.varStack.append(self.loadValue(args["1"]))
    def POPS(self,args):
        if(not self.mem.varStack):
            error(56,"Var stack is empty-cant pops")
        self.mem.writeToVAR(args["1"],self.mem.varStack.pop(-1))
    def ARITMETIC(self,args,operation):
        a=self.loadValue(args["2"])
        b=self.loadValue(args["3"])
        c=None
        if(type(a)!=type(b) or type(a)!=int):
            error(53,"aritmetic operants are not int")
        if(operation=="ADD"):
            c=a+b
        elif(operation=="SUB"):
            c=a-b
        elif(operation=="MUL"):
            c=a*b
        elif(operation=="IDIV"):
            if(b==0):
                error(57,"DIViding by zero is permited")
            c=a//b
        else:
            error(99,"aritmatic selector failed")
        self.mem.writeToVAR(args["1"],c)
    def COMPARISON(self,args,operation):
        a=self.loadValue(args["2"])
        b=self.loadValue(args["3"])
        c=None
        nilComp=(a==None or b==None)
        if(type(a)!=type(b) and not nilComp):
            error(53,"COMPARISON operants are not same")
        if(operation=="EQ"):
            c=a==b
        elif not nilComp:
            if(operation=="LT"):
                c=a<b
            elif(operation=="GT"):
                c=a>b
            else:
                error(99,"aritmatic COMPARISON selector failed")
        else:
            error(53,"nil value can be compered only by equalition")
        self.mem.writeToVAR(args["1"],c)
    def BINARY(self,args,operation):
        a=self.loadValue(args["2"])
        c=None
        if(operation!="NOT"):
            b=self.loadValue(args["3"])
            if(type(a)!=type(b) or type(a)!=bool):
                error(53,"BINARY operants are not bool")
            if(operation=="AND"):
                c=a and b
            elif(operation=="OR"):
                c=a or b
        elif(operation=="NOT"):
            if type(a)!=bool:
                error(53,"BINARY operant is not bool")
            c=not a
        else:
            error(99,"Binary selector failed")
        self.mem.writeToVAR(args["1"],c)
    def INT2CHAR(self,args):
        a=self.loadValue(args["2"])
        c=None
        if type(a)!=int:
            error(53,"INT2CHAR err-operant is not int")
        try:
            c=chr(a)
        except :
            error(58,"INT2CHAR converzion error")
        self.mem.writeToVAR(args["1"],c)
    def STRI2INT(self,args):
        a=self.loadValue(args["2"])
        b=self.loadValue(args["3"])
        c=None
        if type(a)!=str:
                error(53,"STR2INT 2 operant isnt string")
        elif type(b)!=int:
            error(53,"STR2INT 3 operant isnt int")
        try:
            c=ord(a[b])
        except:
            error(58,"STR2INT converzion failed")
        self.mem.writeToVAR(args["1"],c)
    def READ(self,args):  
        c=None
        failed=False
        if(self.inputSource!=None):
            if(self.inputFile==None):
                self.openFile()
            if(not self.inputFileErr):
                try:
                    c=self.inputFile.readline()
                    if type(c)==str and c=='':
                        failed=True
                    else:
                        c= re.sub(r"\n","", c)
                except:
                    failed=True
            else:
                failed=True
        else:
            try:
                c=input()
            except:
                failed=True
        if not failed and type(c)==str:
            if(args["2"].value=="string"):
                c=stringConverter(c)
            elif(args["2"].value=="int" ):
                try:
                    c=int(c)
                except :
                    c=None
            elif(args["2"].value=="bool"):
                c=c.upper()
                if(c=="TRUE"):
                    c=True
                else:
                    c=False
        else:
            self.mem.writeToVAR(args["1"],None)
            return
        self.mem.writeToVAR(args["1"],c)
    def CONCAT(self,args):
        a=self.loadValue(args["2"])
        b=self.loadValue(args["3"])
        c=None
        if (type(a)!=type(b)) or (type(a)!=str):
            error(53,"Concat operants isnt string")
        c=a+b
        self.mem.writeToVAR(args["1"],c)
    def STRLEN(self,args):
        a=self.loadValue(args["2"])
        c=None
        if (type(a)!=str):
            error(53,"STRLEN err- operants isnt string")
        c=len(a)
        self.mem.writeToVAR(args["1"],c)
    def GETCHAR(self,args):
        a=self.loadValue(args["2"])
        b=self.loadValue(args["3"])
        c=None
        if (type(a)!=str or type(b)!=int):
            error(53,"Getchar  operants isnt valid")
        if(len(a)<=b or b<0):
            error(58,"GETCHAR err-Char in string is not reacheble")
        c=a[b]
        self.mem.writeToVAR(args["1"],c)
    def SETCHAR(self,args):
        a=self.loadValue(args["1"])
        b=self.loadValue(args["2"])
        c=self.loadValue(args["3"])
        if (type(a)!=str or type(b)!=int or type(c)!=str):
            error(53,"SETCHAR  operants isnt valid")
        if(c==""):
            error(58,"Getchar  operants isnt valid")
        if(len(a)<=b or b<0):
            error(58,"SETCHAR err-Char in string is not reacheble")
        a=a[:b]+c[0]+a[b+1:]
        self.mem.writeToVAR(args["1"],a)
    def TYPE(self,args):
        a=self.loadValue(args["2"],True)
        if type(a)==int:
            b="int"
        elif type(a)==str:
            b="string"
        elif type(a)==bool:
            b="bool"
        elif a==None:
            b="nil"
        elif type(a)==notInicializet:
            b=""
        else:
            error(99,"unknown var type")
        self.mem.writeToVAR(args["1"],b)
def stringConverter(old):
    new=bytes(old,encoding="utf-8")
    regex = re.compile(rb"\\(\d{1,3})")
    def replace(match):
        return int(match.group(1)).to_bytes(1, byteorder="big")
    new = regex.sub(replace, new)
    new= new.decode("utf-8")
    return new
def parametersParse(argv):  #funkce pro zpracování parametrů
    INPUT=None
    SOURCE=sys.stdin
    if(len(argv)==2 or len(argv)==3):
        for arg in argv[1:] :
            if(arg=="--help"):
                print("Interperet.py-Interpreting code from xml format \nUsege: interpert.py --[options]=[args...] <[input] >[output] 2>[error_log]")
                print("Options:\n--source=\"file\"       =>  select source file \n--input=\"file\"       =>  select input file\n\nif one option missing the data are reading from STDIN")
                exit(0)
            arg=arg.split('=',1)
            if(arg[0]=="--source" and len(arg)==2):
                SOURCE=arg[1]
            elif(arg[0]=="--input" and len(arg)==2):
                INPUT=arg[1]
            else:
                error(10,"wrong parameters, try --help")
    else:
        error(10,"wrong parameters, try --help")
    return INPUT,SOURCE
def xmlTreeParsing(SOURCE):
    try:
        tree=ET.parse(SOURCE)
    except OSError: 
        error(11,"file not found")
    except:
        error(31,"bad xml structure")
    return tree
def programParsing(root):
    if(root.tag!="program"):
        error(32,"root tag err")
    childs=list(root)
    instructions={}
    for child in childs:
        if(child.tag!="instruction"):
            error(32,"unknown child in xml")
        if(not("order" in child.attrib)or not("opcode" in child.attrib)):
            error(32,"missing instruction atribut")
        try:
            order=int(child.attrib["order"])
        except ValueError:
            error(32,"atribut order converzion error")
        if(order<1 or order in instructions):
            error(32,"instruction order in instruction not valid")
        args={}
        for arg in child:
            if(arg.tag[0:3]!="arg"):
                error(32,"unknown format of parameter")
            if(not("type" in arg.attrib)):
                error(32,"missing parameter atribut")
            try:
                ParamOrder=int(arg.tag[3:])
            except ValueError:
                error(32,"atribut order in arg converzion error")
            if(ParamOrder<0 or ParamOrder>3 or arg.tag[3:] in arg):
                error(32,"order of operand is not valid")
            args[arg.tag[3:]]=operant(arg.attrib["type"],arg.text)
        instructions[order]=Instrucrion(child.attrib["opcode"],args)
    array=[]
    for inst in sorted(instructions.items()):
        array.append(inst[1])
    return program(array)
def error(code,massege):
    print(massege, file=sys.stderr) 
    if(code!=0):
        exit(code)

main()




