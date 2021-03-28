#!/usr/bin/env python3

#autor: Jakub Komarek
#login: xkomar33
#ipp- interperet kodu v xml
import sys
import os
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
import re

def main():
    INPUT,SOURCE=parametersParse(sys.argv)      #zpracování parametrů
    tree=xmlTreeParsing(SOURCE)                 #získání ze xml stromovou strukturu
    root=tree.getroot()                         
    MyProgram=programParsing(root)              #zpracování xml stromu 

    MyProgram.firstRun()                        #první průchod programem-kontrola operátárů a jejich parametů(hlavně syntaktické kontroly), zaznammání pozic skoků
    print(MyProgram)
    MyProgram.secondRun()                      #druhý průchod programem-samotné provedení instrukcí
    print(MyProgram.mem)
    error(0,"program run succesfuly")
    exit(0)
class Instrucrion(object):
    Type=""
    args={}
    def __init__(self,op,args):
        op=op.upper()
        self.args=args
        if(op=="RETURN"or op=="CREATEFRAME"or op=="PUSHFRAME"or op=="POPFRAME"or op=="BREAK"):
            self.paramCheck()
        elif(op=="ADD"or op=="SUB"or op=="MUL"or op=="IDIV"or op=="LT"or op=="GT"or op=="EQ"or op=="AND"or op=="OR"or op=="NOT"or op=="STRI2INT"or op=="CONCAT"or op=="GETCHAR"or op=="SETCHAR"):
            self.paramCheck("var","sym","sym")
        elif(op=="MOVE"):
            self.paramCheck("var","sym")
        elif(op=="INT2CHAR"or op=="STRLEN"or op=="type"):
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
            error(21,"Unknown op Code")     
        self.Type=op
    def __repr__(self):
        return "<Instruction - type: %s,\t args:%s >\n" % (self.Type, self.args)
    def paramCheck(self,*args):     #porovnání typů parametrů instrukcí s očekávanými typy
        if(len(args)!=len(self.args)):
            error(-1,"to few or to much paremeters on instruction")
        paramCounter=0
        for arg in args:
            paramCounter+=1
            if(not(str(paramCounter) in self.args)):
                error(32,"parameter not found")
            Type=self.args[str(paramCounter)].Type
            if(arg=="sym"):
                if(not(Type=="bool" or Type=="var" or Type=="string" or Type=="int" or Type=="nil")):
                    error(-1,"arg check error")
            elif(Type!=arg):
                error(-1,"arg check error")

class operant(object):
    Type=""
    value=""
    placement=None
    def __init__(self,Type,value):
        self.Type=Type
        if(self.Type=="var"):
            separated=value.split('@',1)
            if((separated[0]=="GF" or separated[0]=="LF" or separated[0]=="TF")and (separated[1]!="")):
                if not re.match(r"^[A-Za-z_\-$&%*!?][A-Za-z0-9_\-$&%*!?]*$", separated[1]):
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
                value=int(value)
            else:
                error(32,"INT value not valid")
        elif(self.Type=="string"):
            pass
        elif(self.Type=="nil" and value=="nil"):
            value=None
        elif(self.Type=="type"):
            if(not re.match(r"^(nil|bool|int|string)$", value)):
                error(32,"Type invalid")
        elif(self.Type=="label"):
            if(not re.match(r"^([A-Za-z_\-$&%*!?][A-Za-z0-9_\-$&%*!?]*)$", value)):
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
class memory(object):
    GF=frame()
    TF=None
    LF=None
    stack=[]
    def writeToVAR(self,name,frameType,Value):
        if frameType=="GF":
            if not name in self.GF.varS:
                error(52,"Moving destination doesnt exist in GF")
            self.GF.varS[name]=Value
        elif frameType=="LF":
            if not name in stack[-1].varS:
                error(52,"Moving destination doesnt exist in LF")
            elif LF==None:
                error(52,"LF Frame dont exist")
            self.LF.varS[name]=Value
        elif frameType=="TF":
            if not name in self.TF.varS:
                error(52,"Moving destination doesnt exist in TF")
            elif TF==None:
                error(52,"TF Frame dont exist")
            self.TF.varS[name]=Value
        else:
            error(99,"this frame dont exists")
    def readFromVar(self,name,frameType):
        Value=None
        if frameType=="GF":
            if not name in self.GF.varS:
                error(52,"Var  doesnt exist in GF")
            Value=self.GF.varS[name]
        elif frameType=="LF":
            if not name in stack[-1].varS:
                error(52,"Var destination doesnt exist in LF")
            elif LF==None:
                error(52,"LF Frame dont exist")
            Value=self.LF.varS[name]
        elif frameType=="TF":
            if not name in self.TF.varS:
                error(52,"Var destination doesnt exist in TF")
            elif TF==None:
                error(52,"TF Frame dont exist")
            Value=self.TF.varS[name]
        else:
            error(99,"this frame dont exists")
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
            self.GF.varS[var.value]=None
        elif var.placement=="LF":
            if var.value in self.stack[-1].varS:
                error(52,"Defvar err-duplicit name of var in LF")
            elif self.LF==None:
                error(52,"LF Frame dont exist")
            self.stack[-1].varS[var.value]=None
        elif var.placement=="TF":
            if var.value in self.TF.varS:
                error(52,"Defvar err-duplicit name of var in TF")
            elif self.TF==None:
                error(52,"TF Frame dont exist")
            self.TF.varS[var.value]=None
        else:
            error(99,"defvar err")
    def MOVE(self,args):
        self.writeToVAR(args["1"].value,args["1"].placement,args["2"].value,)
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
    instructructions={}
    jTable=jumpTable()
    mem=memory()
    counter=1
    def __init__(self,instructructions):
        self.instructructions=instructructions
    def __repr__(self):
        return "<Program: - instructions:\n %s \nJumptable:\n %s" % (self.instructructions,self.jTable)    
    def firstRun(self):
        for i in range(1, len(self.instructructions)+1):
            if(self.instructructions[str(i)].Type=="LABEL"):
                name=self.instructructions[str(i)].args["1"].value
                if(name in self.jTable.table):
                    error(32,"duplicit label")
                else:
                    self.jTable.table[name]=i
    def secondRun(self):
        while self.counter<=len(self.instructructions):
            self.execute(self.instructructions[str(self.counter)])
            self.counter+=1
    def execute(self,instruction):
        error(0,"executing: %s"%instruction.Type)
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
            pass
        elif instruction.Type=="POPS":
            pass
        elif instruction.Type=="ADD":
            pass
        elif instruction.Type=="SUB":
            pass
        elif instruction.Type=="MUL":
            pass
        elif instruction.Type=="IDIV":
            pass
        elif instruction.Type=="LT":
            pass
        elif instruction.Type=="QT":
            pass
        elif instruction.Type=="EQ":
            pass
        elif instruction.Type=="AND":
            pass
        elif instruction.Type=="OR":
            pass
        elif instruction.Type=="NOT":
            pass
        elif instruction.Type=="INT2CHAR":
            pass
        elif instruction.Type=="STRI2INT":
            pass
        elif instruction.Type=="READ":
            pass
        elif instruction.Type=="WRITE":
            self.WRITE(instruction.args)
        elif instruction.Type=="CONCAT":
            pass
        elif instruction.Type=="STRLEN":
            pass
        elif instruction.Type=="GETCHAR":
            pass
        elif instruction.Type=="SETCHAR":
            pass
        elif instruction.Type=="TYPE":
            pass
        elif instruction.Type=="LABEL":
            pass
        elif instruction.Type=="JUMP":
            self.JUMP(instruction.args)
        elif instruction.Type=="JUMPIFEQ":
            pass
        elif instruction.Type=="JUMPIFNEQ":
            pass
        elif instruction.Type=="EXIT":
            self.EXIT(instruction.args)
        elif instruction.Type=="DPRINT":
            self.DPRINT()
        elif instruction.Type=="BREAK":
            self.BREAK()
        else:
            error(99,"unknow procedure for instruction execution")
    def WRITE(self,args):
        if(args["1"].Type=="var"):
            print(self.mem.readFromVar(args["1"].value,args["1"].placement))
        else:
            print(args["1"].value) 
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
            error(-1,"Jump label isnt in code")
        pass
    def DPRINT(self,args):
        error(0,str(args["1"].value))
    def BREAK(self):
        error(0,"Pozition: %d \n%s"% (self.counter,self))
    def EXIT(self,args):
        retCode=0
        try:
            retCode=int(args["1"].value)
        except:
            retCode=57
        exit(retCode)


def parametersParse(argv):  #funkce pro zpracování parametrů
    INPUT=None
    SOURCE=None
    if(len(argv)==2 or len(argv)==3):
        for arg in argv[1:] :
            if(arg=="--help"):
                print("Interperet.py-Interpreting code from xml format \nUsege: interpert.py --[options]=[args...] <[input] >[output] 2>[error_log]")
                print("Options:\n--source=\"file\"       =>  select source file \n--input=\"file\"       =>  select input file\n\nif one option missing the data are reading from STDIN")
                exit(0)
            arg=arg.split('=',1)
            if(arg[0]=="--source" and arg[1]!=None):
                SOURCE=arg[1]
            elif(arg[0]=="--input" and arg[1]!=None):
                INPUT=arg[1]
            else:
                error(10,"wrong parameters, try --help")
    else:
        error(10,"wrong parameters, try --help")
    return INPUT,SOURCE
def xmlTreeParsing(SOURCE):
    try:
        if (SOURCE!=None):
            tree=ET.parse(SOURCE)
        else :
            tree=ET.parse(sys.stdin)
    except OSError: 
        error(11,"file not found")
    except:
        error(31,"bad xml structure")
    return tree
def programParsing(root):
    if(root.tag!="program"):
        error(32,"root tag err")
    childs=list(root)
    childsLen=len(childs)
    instructions={}
    for child in childs:
        if(child.tag!="instruction"):
            error(32,"unknown child in xml")
        if(not("order" in child.attrib)or not("opcode" in child.attrib)):
            error(32,"missing instruction atribut")
        if(int(child.attrib["order"])<1 or int(child.attrib["order"])>childsLen or child.attrib["order"] in instructions):
            error(32,"instruction order not valid")
        args={}
        for arg in child:
            if(arg.tag[0:3]!="arg"):
                error(32,"unknown format of parameter")
            if(not("type" in arg.attrib)):
                error(32,"missing parameter atribut")
            if(int(arg.tag[3:])<0 or int(arg.tag[3:])>3 or arg.tag[3:] in arg):
                error(32,"order of operand is not valid")
            args[arg.tag[3:]]=operant(arg.attrib["type"],arg.text)
        instructions[child.attrib["order"]]=Instrucrion(child.attrib["opcode"],args)
    return program(instructions)
def error(code,massege):
    print(massege, file=sys.stderr) 
    if(code!=0):
        exit(code)

main()




