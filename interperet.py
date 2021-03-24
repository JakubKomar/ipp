#!/usr/bin/env python3

#autor: Jakub Komarek
#login: xkomar33
#ipp- interperet kodu v xml
import sys
import os
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET

class Instrucrion(object):
    Type=""
    args={}
    def __init__(self,Type,args):
        self.Type=Type
        self.args=args
    def __repr__(self):
        return "<Instruction - type: %s, args:%s >\n" % (self.Type, self.args)
class operant(object):
    Type=""
    value=""
    def __init__(self,Type,value):
        self.Type=Type
        self.value=value
    def __repr__(self):
        return "<Operant - type: %s, value: %s>" % (self.Type, self.value)
class program(object):   
    instructructions={}
    def __init__(self,instructructions):
        self.instructructions=instructructions
    def __repr__(self):
        return "<Program: - instructions:\n %s" % (self.instructructions)    
def parametersParse(argv): 
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
                print("wrong parameters, try --help")
                exit(10)
    else:
        print("wrong parameters, try --help")
        exit(10)
    return INPUT,SOURCE
def xmlTreeParsing(SOURCE):
    try:
        if (SOURCE!=None):
            tree=ET.parse(SOURCE)
        else :
            tree=ET.parse(sys.stdin)
    except FileNotFoundError: 
        print("file not found")
        exit(11)
    except:
        print("bad xml structure")
        exit(31)
    return tree
def programParsing(root):
    if(root.tag!="program"):
        print("root tag err")
        exit(32)
    childs=list(root)
    childsLen=len(childs)
    instructions={}
    for child in childs:
        if(child.tag!="instruction"):
            print("unknown child in xml")
            exit(32)
        if(not("order" in child.attrib)or not("opcode" in child.attrib)):
            print("missing instruction atribut")
            exit(32)
        if(int(child.attrib["order"])<1 or int(child.attrib["order"])>childsLen or child.attrib["order"] in instructions):
            print("instruction order not valid")
            exit(32)
        args={}
        for arg in child:
            if(arg.tag[0:3]!="arg"):
                print("unknown format of parameter")
                exit(32)
            if(not("type" in arg.attrib)):
                print("missing parameter atribut")
                exit(32)
            if(int(arg.tag[3:])<0 or int(arg.tag[3:])>3 or arg.tag[3:] in arg):
                print("order of operand is not valid")
                exit(32)
            args[arg.tag[3:]]=operant(arg.attrib["type"],arg.text)
        instructions[child.attrib["order"]]=Instrucrion(child.attrib["opcode"],args)
    return program(instructions)

INPUT,SOURCE=parametersParse(sys.argv)
tree=xmlTreeParsing(SOURCE)
root=tree.getroot()
MyProgram=programParsing(root)

print(MyProgram)







