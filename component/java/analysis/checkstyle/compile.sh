#!/bin/bash

exec 2>/tmp/error_out
function STOUT(){
    echo "[COUT] $@"
    $@ | awk '{print "[COUT]", $0}'
    if [ "`cat /tmp/error_out`" = "" ]
    then
        return 0
    else
        awk '{print "[COUT]", $0}' /tmp/error_out
        echo '' > /tmp/error_out
        return 1
    fi
}

declare -A map=(
    ["git-url"]="" 
    ["out-put-type"]=""
    ["report-path"]=""
)
data=$(echo $CO_DATA |awk '{print}')
for i in ${data[@]}
do
    temp=$(echo $i |awk -F '=' '{print $1}')
    value=$(echo $i |awk -F '=' '{print $2}')
    for key in ${!map[@]}
    do
        if [ "$temp" = "$key" ]
        then
            map[$key]=$value
        fi
    done
done
if [ "$?" -ne "0" ]
then
    printf "[COUT] CO_RESULT = %s\n" "false"
fi

if [ "" = "${map["git-url"]}" ]
then
    printf "[COUT] Handle input error: %s\n" "git-url"
    printf "[COUT] CO_RESULT = %s\n" "false"
    exit
fi

if [[ "${map["out-put-type"]}" =~ ^(xml|json|yaml)$ ]]
then
    printf "[COUT] out-put-type: %s\n" "${map["out-put-type"]}"
else
    printf "[COUT] Handle input error: %s\n" "out-put-type should be one of xml,json,yaml"
    printf "[COUT] CO_RESULT = %s\n" "false"
    exit
fi

if [ "" = "${map["report-path"]}" ]
then
    map["report-path"]="build/reports/checkstyle"
fi

STOUT git clone ${map["git-url"]}
pdir=`echo ${map["git-url"]} | awk -F '/' '{print $NF}' | awk -F '.' '{print $1}'`
cd ./$pdir
if [ ! -f "build.gradle" ]
then
    printf "[COUT] file build.gradle not found! \n"
    printf "[COUT] CO_RESULT = %s\n" "false"
    exit
fi 

havecheckstyle=`echo gradle -q tasks --all | grep checkstyle`
if [ "$havecheckstyle" = "" ]
then
    echo -e "\napply plugin: 'checkstyle'" >> build.gradle
    mkdir -p ./config/checkstyle
    cp /root/checkstyle.xml ./config/checkstyle/
fi

STOUT gradle checkstyleMain
STOUT gradle checkstyleTest

if [ "${map["out-put-type"]}" = "xml" ]
then
    STOUT cat ${map["report-path"]}/main.xml
    STOUT cat ${map["report-path"]}/test.xml
else
    STOUT java -jar /root/convert.jar ${map["report-path"]}/main.xml ${map["out-put-type"]}
    STOUT java -jar /root/convert.jar ${map["report-path"]}/test.xml ${map["out-put-type"]}
fi

if [ "$?" -eq "0" ]
then
    printf "[COUT] CO_RESULT = %s\n" "true"
fi
