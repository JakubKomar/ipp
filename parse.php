<?php 	
/*
	autor:Jakub Komárek 
	login:xkomar33
	ipp projekt
*/
ini_set('display_errors','stderr');
define('HeadErrCode',21);
define('OpErrCode',22);
define('SynErrCode',23);
define('ParamErrCode',10);

$order=0;	//pořadí instrukce
$row=0;	//číslo řádku pro výpis chyby
$head=FALSE;//byla nalezena hlavička na vstupu	

if($argc!=1)
{
	if($argc==2&&$argv[1]=="--help")
	{
		fprintf(STDOUT,"Usage: php7.4 ./parse.php [options] [args...] <[input] >[output] 2>[error_log]\nProgram parsing code in IPP21 to xml format and checking syntax and sematic\n");
		exit(0);
	}
	else
	err(10);
}
while ($line=fgets(STDIN))
{
	$row++;
	$line=preg_replace('/^[\s|\t]+/','',$line);	//odstranění mezer a tabelátorů na začátku řádku
	$line=preg_replace('/[\s|\t]+/',' ',$line);	//odstranění několikanásobných mezer a tabelátorů mezi výrazy. Poté nahrazeno pouze jendou mezerou 
	$line=preg_replace('/(([\s|\t]*)|([\s|\t]*#.*))$/','',$line);	//odstranění tabelátorů, mezer , komentářů  na konci řádku

	if(!strcmp($line,""))	//prázdný řádek kódu
		continue;

	$split=explode(' ',$line); 	//rozdělení na jednotlivé výrazy + odstranění konce řádků 
	
	if($head==FALSE)	//identifikátor hlavičky
	{	
		if(!strcmp(strtoupper($split[0]),".IPPCODE21"))
		{
			$head=TRUE;
			if(count($split)>1)	//pokud je za hlavičkou něco jiného než komentář ->chyba
				err(HeadErrCode);	
			else
				generateXmlHead();
		}
		else
			err(HeadErrCode);
	}
	else
		analyzeOp($split,$order);	
}
if(!$head)
	err(HeadErrCode);
generateXmlEnd();
exit(0);

	function analyzeOp($split,&$order)
	{
		$order++;
		$split[0]=strtoupper($split[0]);	//operátory jsou caseinsezitive
		fprintf(STDOUT,"\t<instruction order=\"$order\" opcode=\"$split[0]\">\n");//výpis instrukce
		switch ($split[0]) {
			case "RETURN":
			case "CREATEFRAME":
			case "PUSHFRAME":
			case "POPFRAME":
			case "BREAK":
				analyzeParams($split);	
				break;	
			case "ADD":
			case "SUB":
			case "MUL":
			case "IDIV":
			case "LT":
			case "GT":
			case "EQ":
			case "AND":
			case "OR":
			case "STRI2INT":	
			case "CONCAT":
			case "GETCHAR":
			case "SETCHAR":	
				analyzeParams($split,"VAR","SYM","SYM");
				break;
			case "NOT":
			case "MOVE":
				analyzeParams($split,"VAR","SYM");
				break;
			case "INT2CHAR":
			case "STRLEN":	
			case "TYPE":
				analyzeParams($split,"SYM","SYM");
				break;
			case "DEFVAR":				
			case "POPS":
				analyzeParams($split,"VAR");
				break;
			case "JUMPIFEQ":
			case "JUMPIFNEQ":
				analyzeParams($split,"LABEL","SYM","SYM");
				break;
			case "LABEL":	
			case "CALL":			
			case "JUMP":
				analyzeParams($split,"LABEL");
				break;
			case "PUSHS":	
			case "WRITE":
			case "EXIT":
			case "DPRINT":
				analyzeParams($split,"SYM");
				break;
			case "READ":
				analyzeParams($split,"VAR","TYPE");
				break;
			default:
				fprintf(STDERR,"Unknown op Code\n");
				err(OpErrCode);
				break;
		}
		fprintf(STDOUT,"\t</instruction>\n");
	}  
	function analyzeParams($Split,...$params)
	{	
		$Nparam=1;		//pozice parametru  
		foreach($params as $param)	//zkontrolují se všechny zadané parametry do funkce
		{	
			$type;	//typ, který se vypíše do xml
			$textpart=$Split[$Nparam];//defalutně se vypisuje celý	
			switch ($param) 	//podle zdaného typu, který by se měl nacházet za operátory se vyberou lexikální a syntaktická pravidla na kontrolu
			{
				case "VAR":	
					if(!preg_match('/^((LF|GF|TF)@[A-Za-z_\-$&%*!?][A-Za-z0-9_\-$&%*!?]*)$/',$Split[$Nparam]))
					{
						fprintf(STDERR,"Variable format is wrong\n");
						err(SynErrCode);
					}
					$type="var";
					break;
				case "SYM":
					if(!preg_match('/^((LF|GF|TF)@[A-Za-z_\-$&%*!?][A-Za-z0-9_\-$&%*!?]*)$/',$Split[$Nparam]))	//pokud výraz není proměná
					{	
						$parts=explode('@',$Split[$Nparam],2);	//rozdělení na typovou a datovou část
						switch ($parts[0]) 
						{
							case "bool":
								if($parts[1]!="true"&&$parts[1]!="false")
								{
									fprintf(STDERR,"Unknown bool value\n");
									err(SynErrCode);
								}
								$type="bool";
								break;
							case "int":
								if(!preg_match('/^[\+\-\d]*$/',$parts[1]))
								{
									fprintf(STDERR,"Used bad characters in int value\n");
									err(SynErrCode);
								}
								if(!preg_match('/^((\+|\-)?(0|[1-9][0-9]*))$/',$parts[1]))
									err(SynErrCode);	//v zadání bylo stanoveno, nekontrolovat správnost int hodnoty->pouze varování
								$type="int";
								break;
							case "string":
								if(preg_match('/(\\\\\D..)|(\\\\.\D.)|(\\\\..\D)|(\\\\..$)|(\\\\.$)|(\\\\$)/',$parts[1]))//nesprávné escape sekvence
								{
									fprintf(STDERR,"Escape secuence not valid\n");
									err(SynErrCode);
								}
								$type="string";
								break;
							case "nil":
								if($parts[1]!="nil")
								{
									fprintf(STDERR,"Nil value wrong\n");
									err(SynErrCode);
								}
								$type="nil";
								break;					
							default:
								fprintf(STDERR,"Unknown data type\n");
								err(SynErrCode);
								break;
						}	
						$textpart=$parts[1];//v případě konstanty pouze část
					}
					else
						$type="var";
					break;
				case "TYPE":
					if(!preg_match('/^(nil|bool|int|string)$/',$Split[$Nparam]))
					{
						fprintf(STDERR,"Unknown type\n");
						err(SynErrCode);
					}
					$type="type";						
					break;
				case "LABEL":	
					if(!preg_match('/^([A-Za-z_\-$&%*!?][A-Za-z0-9_\-$&%*!?]*)$/',$Split[$Nparam]))
					{
						fprintf(STDERR,"Label wrong format\n");
						err(SynErrCode);
					}
					$type="label";
					break;
				default:
					fprintf(STDERR,"Function AnalyzeParam called whith bad parameter\n");
					err(99);
					break;
			}
			$textpart=convertStringToXML($textpart);
			fprintf(STDOUT,"\t\t<arg$Nparam type=\"$type\">$textpart</arg$Nparam>\n");	
			$Nparam++;
		}
		if(count($Split)>$Nparam)
		{
			fprintf(STDERR,"to much parametes for op code\n");
			err(SynErrCode);
		}
	}
	function convertStringToXML($string)
	{
		$string=preg_replace('/%/',"%%",$string);//nahrazení %
		$string=preg_replace('/&/',"&amp;",$string);//nahrazení &
		$string=preg_replace('/</',"&lt;",$string);	//nahrazení <
		$string=preg_replace('/>/',"&gt;",$string);	//nahrazení >
		$string=preg_replace('/"/',"&quot;",$string);	//nahrazení "
		$string=preg_replace('/>/',"&apos;",$string);	//nahrazení '
		return($string);
	}
	function generateXmlHead()
	{
		fprintf(STDOUT,"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<program language=\"IPPcode20\">\n");		
	}
	function generateXmlEnd()
	{
		fprintf(STDOUT,"</program>\n");
	}
	function err($errCode){
		$massege;
		global $row;
		switch ($errCode) {
			case HeadErrCode:
				$massege="Invalid Header on line: $row";
				break;
			case OpErrCode:
				$massege="Invalid Operand on line: $row";
				break;
			case SynErrCode:
				$massege="Syntax or Sematic Err on line: $row";
				break;	
			case ParamErrCode:
				$massege="Parameters are not valid";
				break;	
			default:
				$massege="Unamed Error";
				break;
		}
		fprintf(STDERR,$massege."\n");
		exit($errCode);
	}
	
?>