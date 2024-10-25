#!/bin/bash

function usage {
    echo "
Usage: script_name [options] design_file

Options:
-h, --help: Display this help information and exit.
-t, --toSdc: Specify the sgdc file to convert the design to SDC format.
-s, --script: Specify the ecdc tool running with '-s' option.
-i, --init: Specify the ecdc tool running with '-init' option.
-p, --path: Specify the output directory for the SDC file.
--ecdc: Specify the path to the ecdc executable.
-v, --verilog: Specify the Verilog design file.
-f, --f_design: Specify the design list file.

Example:
./script_name -t design.sgdc
./script_name -i design.sgdc
./script_name -t design.sgdc -p /path/to/output
./script_name --ecdc /path/to/ecdc

The script will generate a sdc file based on the sgdc file. The SDC file generated will be moved to the specified output directory if provided.
"
}

# Define the variable default value
design_file=""
designType="v"
ecdcPath="/mnt/efs/fs1/jenkins/build/today/build_Release/Release/package_ecdc/AppDir/ecdc-x86_64.AppImage"
output_dir=""

# Use getopt correctly
getopt_cmd=$(getopt -o ht:s:i:p:v:f --long help,toSdc:,script:,init:,path:,ecdc:,verilog:,f_design -n $(basename $0) -- "$@")
[ $? -ne 0 ] && exit 1
eval eval set -- "$getopt_cmd"

# Process the options
while [ -n "$1" ]; do
    case "$1" in
        -h|--help)
            usage
            exit ;;
        -t|--toSdc)
            type="-t"
            sgdc_file="$2"
            shift 2 ;;
        -s|--script)
            type="-s"
            sgdc_file="$2"
            shift 2 ;;
        -i|--init)
            type="-i"
            sgdc_file="$2"
            shift 2 ;;
        -p|--path)
            output_dir="$2"
            shift 2 ;;
        --ecdc)
            ecdcPath="$2"
            shift 2 ;;
        -v|--verilog)
            design_file="$2"
            shift 2 ;;
        -f|--f_design)
            designType="f"
            shift ;;
        --)
            shift
            break ;;
        *)
            echo "$1 is not a valid option"
            exit 1 ;;
    esac
done
        

# Define the script path
script_path=$(dirname "$(realpath "$0")")

case_file=`dirname ${sgdc_file}`
if [ -z $design_file ]; then
    if [ $designType == "v" ]; then
        design_file=`find $case_file -maxdepth 1 -name "*.v"`
    elif [ $designType == "f" ]; then
        design_file=`find $case_file -maxdepth 1 -name "*.f"`
    fi
elif [ -n $design_file ]; then
    if [ -e $design_file ]; then
        :
    else
        echo -e "\e[31mERROR: Invalid input file: $design_file\e[0m"
        exit 1
    fi
fi

if [ $designType == "v" ]; then
    case_name=`basename $design_file ".v"`
elif [ $designType == "f" ]; then
    case_name=`basename $design_file ".f"`
fi

# Generate the script based on the options
if [ "${type}" = "-t" ]; then
    echo "read_design -sysv $design_file
    source ${script_path}/proc_sgdc.tcl
    source ${script_path}/cfg/ecdc_cfg
    set $genericParams::toSdc 1
    read_sgdc ${sgdc_file}" > trans_test_sgdc.tcl

    $ecdcPath -s trans_test_sgdc.tcl > /dev/null
    rm trans_test_sgdc.tcl
elif [ "${type}" = "-s" ]; then
    echo "read_design -sysv $design_file
    source ${script_path}/proc_sgdc.tcl
    source ${script_path}/cfg/ecdc_cfg
    read_sgdc ${sgdc_file}
    check_cdc" > run_sgdc.tcl

    $ecdcPath -s run_sgdc.tcl
    rm run_sgdc.tcl
elif [ "${type}" = "-i" ]; then
    echo "read_design -sysv $design_file
    source ${script_path}/proc_sgdc.tcl
    source ${script_path}/cfg/ecdc_cfg
    read_sgdc ${sgdc_file}
    check_cdc" > run_sgdc.tcl

    $ecdcPath -init run_sgdc.tcl
    rm run_sgdc.tcl
fi

# Move the SDC file
if [ -z "$output_dir" ]; then
    :
elif [ -n "$output_dir" ]; then
    mv ${case_name}.sdc "$output_dir"
fi
