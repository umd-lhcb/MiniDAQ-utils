#!/usr/bin/env bash
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Fri Jan 17, 2020 at 04:30 AM -0500

GBT=0

declare -A ELK_CHS=(
    [3]="11 10 9"
    [2]="8 7 6"
    [1]="5 4 3"
    [0]="2 1 0"
)

declare -A MINIDAQ_CHS=(
    [1]=22
    [2]=12
    [3]=23
    [4]=21
    [5]=14
    [6]=13
)

case $1 in
    FH) # On Mirror BP, we are using JP9 and JD10
        ./dcbutil.py init ./gbtx_config/slave-Tx-wrong_termination.txt -g $GBT

        GBTXS=( 3 4 5 )
        declare -A I2C_BUS=(
            [3]=2
            [4]=1
            [5]=0
        )

        for bus in ${I2C_BUS[@]}; do
            ./saltutil.py $bus init -g $GBT
        done

        # Now we start adjusting phase
        for gbtx in ${GBTXS[@]}; do
            echo "Validating GBTx $gbtx..."
            for asic in 3 2 1; do
                ./phaseadj.py -g $GBT -s $gbtx \
                    -b ${I2C_BUS[$gbtx]} -a $asic -e ${ELK_CHS[$asic]} \
                    --adjust-elink-phase y \
                    --adjust-tfc-phase n \
                    --non-verbose
            done
            # Print out the final result for each GBTx
            ./phaseadj.py -g $GBT -s $gbtx \
                -b ${I2C_BUS[$gbtx]} -a 0 -e ${ELK_CHS[0]} \
                --adjust-elink-phase y \
                --adjust-tfc-phase n
        done
        ;;

    SH) # On Mirror BP, we are using JP10 and JD10
        ./dcbutil.py init ./gbtx_config/slave-Tx-wrong_termination.txt -g $GBT

        GBTXS=( 1 2 6 )
        declare -A I2C_BUS=(
            [1]=4
            [2]=3
            [6]=5
        )

        for bus in ${I2C_BUS[@]}; do
            ./saltutil.py $bus init -g $GBT
        done

        # Now we start adjusting phase
        for gbtx in ${GBTXS[@]}; do
            echo "Validating GBTx $gbtx..."
            for asic in 3 2 1; do
                ./phaseadj.py -g $GBT -s $gbtx \
                    -b ${I2C_BUS[$gbtx]} -a $asic \
                    -c ${MINIDAQ_CHS[$gbtx]} \
                    -e $(echo ${ELK_CHS[$asic]}) \
                    --adjust-elink-phase y \
                    --adjust-tfc-phase n \
                    --non-verbose
            done
            # Print out the final result for each GBTx
            ./phaseadj.py -g $GBT -s $gbtx \
                -b ${I2C_BUS[$gbtx]} -a 0 \
                -c ${MINIDAQ_CHS[$gbtx]} \
                -e $(echo ${ELK_CHS[0]}) \
                --adjust-elink-phase y \
                --adjust-tfc-phase n
        done
        ;;

    *)
        echo "Unknown option: $1."
        ;;

esac
