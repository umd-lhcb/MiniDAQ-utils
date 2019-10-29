# MiniDAQ-utils
MiniDAQ utilities for programming and controlling DCB and SALT.

## To program all data GBTxs
```
cd ~/src/MiniDAQ-utils/dcb
./dcb_data_write.py 0 ~/src/gbtx_config/slave-Tx-wrong_termination.txt
```

## To turn on/off DCB PRBS
```
cd ~/src/MiniDAQ-utils/dcb
./dcb_data_write.py prbs on|off
```

## To program a single 4-ASIC group (4 SALTs)
```
cd ~/src/MiniDAQ-utils/salt
./salt_write.py init 5
```

Note that `5` is the I2C address.

## To adjust phase of a single 4-ASIC group
```
cd ~/src/MiniDAQ-utils/salt
./salt_write.py append 5 --phase 16
```

## To ask SALT to generate PRBS 0
```
cd ~/src/MiniDAQ-utils/salt
./salt_write.py append 5 --ser-src 03
```
