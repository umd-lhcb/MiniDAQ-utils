# Comments on the `gbtserv` source code

This documentation applies to `gbtserv` `6.2.11`. The source code is available at:
https://gitlab.cern.ch/lhcb-readout40/software/gbtserv.git


## DIM command parsing
The parsing of DIM commands is defined in `src/GbtCommon.c`:

```c
int parseOpPars(REGISTER_SETTINGS_STRUCT *reg, char *address, U8 (*tmp)[MAX_PARAMETER_SIZE])
{
  int i, j, k, id;

  // printf("reg->done = %d\n", reg->done);
  if (reg)
  {
	  if ((reg->lenOut != -1) && (reg->done != -2))
		  return 0;
	  reg->lenOut = -1;
  }
	for (i = 0, j = 0, k = 0; i < (int)strlen(address) + 1 && j < MAX_SETTINGS; i++)
	{
		if(address[i] == ',' || i == (int) strlen(address))
		{
			tmp[j][k] = '\0';
			k = 0;
			j++;
		}
		else
		{
			if (k < MAX_PARAMETER_SIZE)
			{
				tmp[j][k] = address[i];
				k++;
			}
		}
	}
	if (reg)
	{
		reg->connection = 0;
		//	reg->gbtID = atoi(tmp[1]);
		reg->oper = atoi(tmp[0]);
		configGetRealMasterId(atoi(tmp[1]), &id);
		reg->gbtID = id;
		reg->scaID = atoi(tmp[2]);
		reg->scaVer = 1;
	}
	return j;
}
```

The takeaways are:

1. The parameters are separated by `,`
2. `address` is the DIM command to be parsed.
3. The ordering of the parameters:
    1. Operation mode
    2. GBT ID (translated by `configGetRealMasterId`, which is defined in `src/GbtCommon.c`)
    3. SCA ID
4. It is interesting that here the `scaVer` is hard-coded to 1.
