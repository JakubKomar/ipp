#!/usr/bin/env python3

#autor: Jakub Komarek
#login: xkomar33
#ipp- interperet kodu v xml
import sys
import os
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET

def main():
    INPUT,SOURCE=parametersParse(sys.argv)      #zpracování parametrů
    tree=xmlTreeParsing(SOURCE)                 #získání ze xml stromovou strukturu
    root=tree.getroot()                         
    MyProgram=programParsing(root)              #zpracování xml stromu 

    print(MyProgram)
    MyProgram.firstrun()                        #první průchod programem-kontrola operátárů a jejich parametů(hlavně syntaktické kontroly), zaznammání pozic skoků
    #MyProgram.secondrun()                      #druhý průchod programem-samotné provedení instrukcí

    error(0,"program run succesfuly")
    exit(0)
class Instrucrion(object):
    Type=""
    args={}
    def __init__(self,Type,args):
        self.Type=Type.upper()
        self.args=args
    def __repr__(self):
        return "<Instruction - type: %s,\t args:%s >\n" % (self.Type, self.args)
    def selfCheck(self):    #syntaktická kontrola instrukcí
        op=self.Type
        if(op=="RETURN"or op=="CREATEFRAME"or op=="PUSHFRAME"or op=="POPFRAME"or op=="BREAK"):
            self.paramCheck()
        elif(op=="ADD"or op=="SUB"or op=="MUL"or op=="IDIV"or op=="LT"or op=="GT"or op=="EQ"or op=="AND"or op=="OR"or op=="NOT"or op=="STRI2INT"or op=="CONCAT"or op=="GETCHAR"or op=="SETCHAR"):
            self.paramCheck("VAR","SYM","SYM")
        elif(op=="MOVE"):
            self.paramCheck("VAR","SYM")
        elif(op=="INT2CHAR"or op=="STRLEN"or op=="TYPE"):
            self.paramCheck("SYM","SYM")
        elif(op=="DEFVAR"or op=="POPS"):
            self.paramCheck("VAR")
        elif(op=="JUMPIFEQ"or op=="JUMPIFNEQ"):
            self.paramCheck("LABEL","SYM","SYM")
        elif(op=="LABEL"or op=="CALL"or op=="JUMP"):
            self.paramCheck("LABEL")
        elif(op=="PUSHS"or op=="WRITE"or op=="EXIT"or op=="DPRINT"):
            self.paramCheck("SYM")
        elif(op=="READ"):
            self.paramCheck("VAR","TYPE")
        else:
            error(21,"Unknown op Code")
    def paramCheck(self,*args):     #porovnání typů parametrů instrukcí s očekávanými typy
        if(len(args)!=len(self.args)):
            error(-1,"to few or to much paremeters on instruction")
        paramCounter=0
        for arg in args:
            paramCounter+=1
            if(not(str(paramCounter) in self.args)):
                error(32,"parameter not found")
            Type=self.args[str(paramCounter)].Type
            if(arg=="SYM"):
                if(not(Type=="BOOL" or Type=="VAR" or Type=="STRING" or Type=="INT" or Type=="NIL")):
                    error(-1,"arg check error")
            elif(Type!=arg):
                error(-1,"arg check error")
class operant(object):
    Type=""
    value=""
    placement=None
    def __init__(self,Type,value):
        self.Type=Type.upper()
        if(self.Type=="VAR"):
            separated=value.split('@',1)
            if((separated[0]=="GF" or separated[0]=="LF" or separated[0]=="TF")and (separated[1]!="")):
                value=separated[1]
                self.placement=separated[0]
            else:    
                error(32,"Varieble format not valid")     
        self.value=value
    def __repr__(self):
        return "<Operant - type: %s, value: %s>" % (self.Type, self.value)
class program(object):   
    instructructions={}
    def __init__(self,instructructions):
        self.instructructions=instructructions
    def __repr__(self):
        return "<Program: - instructions:\n %s" % (self.instructructions)    
    def firstrun(self):
        for i in range(1, len(self.instructructions)+1):
            self.instructructions[str(i)].selfCheck()
        return
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
    exit(code)

main()




