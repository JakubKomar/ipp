<?php 	
    /*
        autor:Jakub Komárek 
        login:xkomar33
        ipp projekt
    */
    $files=array(   //cesty k externím souborům
        "dir"           =>"./",
        "parseScript"   =>"./parse.php",
        "intScript"     =>"./interpret.py",
        "jexamxml"      =>"/pub/courses/ipp/jexamxml/jexamxml.jar",
        "jexamcfg"      =>"/pub/courses/ipp/jexamxml/options",
        );
    $parse_only=FALSE;
    $int_only=FALSE;
    $longopts  = array(
        "help", 
        "directory:",   
        "recursive",     
        "parse-script:",   
        "int-script:",    
        "parse-only",    
        "int-only",    
        "jexamxml:",     
        "jexamcfg:",     
    );
    $options = getopt("", $longopts); 
    if(isset($options["help"]))	       
    {
        if( $argc == 2)	
        {
            fprintf(STDOUT,"Usage: php7.4 ./test.php --[options]=[args...] <[input] >[output] 2>[error_log]
    Testing program for parse.php and interpret.py

    options:
        --directory=\"dir\"       =>  select dir whith tests (defalut is root dir.)   
        --recursive             =>  serching for tests in subdirectories    
        --parse-script=\"file\"   =>  select parsing script (defalut parse.php)
        --int-script            =>  select iterpret script (defalut iterpret.py)
        --parse-only            =>  only checking correct working of parser
        --int-only              =>  only checking correct working of interpert
        --jexamxml=\"file\"       =>  pozition of A7Soft JExamXml tool for comparing xml format (defalut /pub/courses/ipp/jexamxml/jexamxml.jar)
        --jexamcfg=\"file\"       =>  pozition of A7Soft JExamXml tool configuration (defalut /pub/courses/ipp/jexamxml/options)\n" );      
            exit(0);
        }
        else
        {
            fprintf(STDERR,"Parameter help cant be combinated whit other paramaters\n");
            err(10);
        }
    }
    elseif(isset($options[ "parse-only"])&&(isset($options[ "int-only"])||isset($options[ "int-script"])) ||  isset($options[ "int-only"])&&(isset($options[ "parse-only"])||isset($options["parse-script"])))
    {//zakázané kombinace parametrů
        fprintf(STDERR,"Combination of parameters is not valid\n");
        err(10);
    }
    else    
    {
        if(isset($options["directory"]))    //měnění defalutní cesty k testům
        {
            $files["dir"]=$options["directory"];
            if(!is_dir($files["dir"]))
            {
                fprintf(STDERR,"Directory didnt exist\n");
                exit(41);
            }
        }
        
        if(isset($options[ "recursive"]))    //získávání souborů z testy
            exec("find " . $files["dir"] . " -regex '.*\.src$'", $testPaths);
        else
            exec("find " . $files["dir"] . " -maxdepth 1 -regex '.*\.src$'", $testPaths);

        if(isset($options[ "parse-script"]))    //změna parsovacího scriptu
            $files["parseScript"]=$options["parse-script"];  
        if(isset($options[ "int-script"]))      //změna intrerpretu
            $files["intScript"]=$options["int-script"]; 

        if(isset($options[ "parse-only"]))      
            $parse_only=TRUE;

        if(isset($options[ "int-only"]))        
            $int_only=TRUE;     

        if(isset($options["jexamxml"]))     //xml analizator
            $files["jexamxml"]=$options["jexamxml"];   

        if(isset($options[ "jexamcfg"]))    //konfigurační soubor
            $files["jexamcfg"]=$options["jexamcfg"];  
        
        if(!$int_only&&(!file_exists($files["jexamcfg"])||!file_exists($files["jexamxml"])))
        {
            fprintf(STDERR,"Jaxam files path are wrong\n");
            exit(41);
        }
        if((!$int_only)&&(!file_exists($files["parseScript"])))
        {
            fprintf(STDERR,"Parse script file didnt exist\n");
            exit(41);
        }
        if((!$parse_only)&&(!file_exists($files[ "intScript"])))
        {
            fprintf(STDERR,"Interperet script file didnt exist\n");
            exit(41);
        }
    }
    $failcounter=0;     //počty úspěšných testů
    $succescounter=0;   //počty neúspěšných testů
    $succsesTests=array();  //pole s cestami úspěšných testů
    $failedTests=array();   //pole s cestami neúspěšných testů
    foreach ($testPaths as $src) {
        $src=preg_replace('/.src$/','',$src);
        $in = $src . ".in";     //vstupní parametry
        $out = $src . ".out";   //očekávaný výstup
        $rc = $src . ".rc";      //vstupní kód
        $erv= 0;                 //očekáváná návratová hodnota
        $failed=FALSE;          //příznak, zda test prošel
        
        if (!file_exists($in)) {
            $file = fopen($in, "w");
            fclose($file);
        }
        $input=file_get_contents($in);      //získání vstupních parametrů pro zapnutí programu
        if (!file_exists($out)) {
            $file = fopen($out, "w");
            fclose($file);
        }
        if (!file_exists($rc)) {
            $file = fopen($rc, "w");
            fwrite($file, "0");
            fclose($file);
        }
        else {
            $file = fopen($rc, "r");
            $erv = intval(fread($file, filesize($rc)));
            fclose($file);
        }

        if($parse_only)  //pouze parsovací část
        {
            exec("php7.4 ".$files["parseScript"]." <".$src.".src 2>/dev/null >temporary.xml",$output , $rv);     //spuštění parsovacího skrtiptu
            if($rv==$erv)   //očekávaná návratová hodnota porovnána se získanou
            {
                if($rv==0)   //pokud je nulová je nutno porovnat výstup
                {
                    exec("java -jar ".$files["jexamxml"]." temporary.xml ".$out." /dev/null ".$files["jexamcfg"],$output,$analyzerRV);     //porovnání xml formátu s předlohou
                    if($analyzerRV) //pokud nebyla nalezena shoda
                    {
                        $failcounter++;
                        $failed=TRUE;
                    }
                    else
                        $succescounter++;
                }
                else    //jinak není potřeba porovnávat výstup
                {
                    $succescounter++;
                }
            }
            else
            {
                $failcounter++;
                $failed=TRUE;
            }
        }
        elseif($int_only)  //pouze iterpretační část
        {
            exec("python ".$files["intScript"]." ".$input." <".$src.".src 2>/dev/null >temporary.code",$output , $rv);              //iterpretace
            if($rv!=0)
            {
                if($erv==$rv)
                    $succescounter++;
                else
                {
                    $failcounter++;
                    $failed=TRUE;
                }
            }
            else
            {
                exec("diff ".$out." temporary.code",$output , $rv);
                if($rv)
                {
                    $failcounter++;
                    $failed=TRUE;
                }
                else
                    $succescounter++;
            }
        }
        else    //obojí
        {   
            exec("php7.4 ".$files["parseScript"]." <".$src.".src 2>/dev/null >temporary.xml",$output , $rv);             //parsování
            if($rv!=0)
            {
                if($erv==$rv)
                    $succescounter++;
                else
                {
                    $failcounter++;
                    $failed=TRUE;
                }
            }
            exec("python ".$files["intScript"]." ".$input." --source=temporary.xml 2>/dev/null >temporary.out",$output , $rv);              //iterpretace
            if($rv!=0)
            {
                if($erv==$rv)
                    $succescounter++;
                else
                {
                    $failcounter++;
                    $failed=TRUE;
                }
            }
            else
            {
                exec("diff ".$out." temporary.out",$output , $rv);
                if($rv)
                {
                    $failcounter++;
                    $failed=TRUE;
                }
                else
                    $succescounter++;
            }
        }
        if($failed)
            array_push($failedTests,$src);
        else
            array_push($succsesTests,$src);

    }

    //generování html výstupu
    generate_html_head();
    fprintf(STDOUT,"\t\t<div class=\"suc\"><h2>Passed :  ".$succescounter."</h2></div>
        <div class=\"fail\"><h2>Failed :  ".$failcounter."</h2><hr></div>
        <div class=\"fail\"><h2>Failed tests:</h2></div>\n");
    generate_list($failedTests);
    fprintf(STDOUT,"<hr><div class=\"suc\"><h2>Passed tests:</h2></div>\n");
    generate_list($succsesTests);
    generate_html_fotter();

    exit(0);
    function generate_list($Tests)
    {   
        $dir;
        foreach ($Tests as $test) { 
            $actualdir=explode('/',$test);
            $name=array_pop($actualdir);    //oddělení jména souboru
            $actualdir=implode("/",$actualdir);
            if($actualdir!=$dir)
            {
                fprintf(STDOUT,"<h3>".$actualdir."</h3>\n");
                $dir=$actualdir;
            }
            fprintf(STDOUT,"<p>".$name."</p>\n");
        }
    }
    function generate_html_head(){
        fprintf(STDOUT,"<!DOCTYPE html>\n<html lang=\"cs\">
        <head>
        <title>Test summary</title>
        <meta charset=\"UTF-8\">
        <style>
        body{
            background-color:white;
            font-family: Arial;
            max-width: 70%%;
            margin: auto;
        }
        .obsah{
            background-color:rgb(255, 195, 155);
        }
        h1{
            margin-top:0px;
            padding-top:10px;
        }
        .suc{
            color:green;
        }
        .fail{
            color: red;
        }
        p{
            margin:5px;
            padding-left:50px;
        }
        h3{
            margin-bottom:5px;
            padding-left:20px;
        }
        </style>        
        </head>
        <body>
        <h1>Tests sumary</h1>");
    }
    function generate_html_fotter(){
        fprintf(STDOUT,"\t</body>\n</html>\n");
    }
    function err($errCode){
		$massege;
		switch ($errCode) {
			default:
				$massege="Unamed Error";
				break;
		}
		fprintf(STDERR,$massege."\n");
		exit($errCode);
	}
?>