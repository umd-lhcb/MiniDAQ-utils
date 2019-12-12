# nanoDAQ
nanoDAQ implements a small fraction of MiniDAQ's functionality in Python.
Currently, the implemented functions are:

* GBT I2C
* GBT GPIO

On our server `UMDlab`, this project should be in `$HOME/src/nanoDAQ`.


## Installation
Only CentOS 7 is supported. To install:
```
cd utils
./install.sh --user  # Install required Python dependencies in user home
```

Note that this script will try to install required `rpm` pacakges, so sudo
permission is needed.


## `dcbutil.py`
**Note**: The following flags are available in most sub-commands:

* `-g` or `--gbt`: GBT index, default to `0`.
* `-s` or `--slaves`: Slaves to be programmed, default to `1 2 3 4 5 6`.

When in doubt, use `-h` of each sub-command for help.

### To program all data GBTxs on GBT 3
```
./dcbutil.py init ./gbtx_config/slave-Tx-wrong_termination.txt -g 3
```

### To program data GBTxs 1 and 2 on GBT 3
```
./dcbutil.py init ./gbtx_config/slave-Tx-wrong_termination.txt -g 3 -s 1 2
```

### To write register `0x1c` with a value of `0x01` to all data GBTxs on GBT 3
```
./dcbutil.py write 1c 1 -g 3
```

### To read 4 registers starting from `0x1c` on all data GBTxs
```
./dcbutil.py read 1c 1
```

### To turn on/off PRBS of slave 1 and 3
```
./dcbutil.py prbs on|off -s 1 3
```

### To check DCB status
```
./dcbutil.py status
```

### To check GPIO status
```
./dcbutil.py gpio
```

### To do a manual reset on GPIO line 3 and 4
```
./dcbutil.py gpio --reset 3 4
```

### To check GBLD bias current
```
./dcbutil.py bias_cur
```

### To set GBLD bias current to 7 mA of GBLD on GBTx 1
```
./dcbutil.py bias_cur 7 -s 1
```


## `saltutil.py`
**Note**: The following flags are available in most sub-commands:

* `-g` or `--gbt`: GBT index, default to `0`.
* `-a` or `--asics`: ASICs to be programmed, default to `0 1 2 3` (**WEST**).

## To program a single hybrid on I2C 5
```
./saltutil.py 5 init
```

Note that the SALT will be GPIO-reset automatically when `init`. Also, `5` is
the I2C bus. This argument is **mandatory**.

## To program SALT `0x0` `0x8` with value `0x1122` on SALTs 1 and 3, I2C 5
```
./saltutil.py 5 write 0 8 1122 -s 1 3
```

## To read 2 SALT registers starting from `0x0` `0x8` on all SALTs, I2C 5
```
./saltutil.py 5 read 0 8 2
```

## To adjust phase to `0x3` of a hybrid on GBT 3, I2C 5
```
./saltutil.py 5 phase 3 -g 3
```

## To change hybrid serializer source to fixed/prbs/tfc on GBT 3, I2C 5
```
./saltutil.py 5 ser_src fixed|prbs|tfc -g 3
```
