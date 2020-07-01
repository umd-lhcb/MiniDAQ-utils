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
5. The `reg` array will store all `,`-delimited parameters


## I2C operation
The I2C operation is defined in `src/GbtI2C.c`:

```c
void cmndI2COperation(long *tag, char *address, int *size)
{
	U8  tmp[MAX_SETTINGS][MAX_PARAMETER_SIZE];
	char  msg[MAX_TMP_SIZE];
	int i;
	int len;
	U8 *data, *p;
	int dataSize;
	int file_flag = 0, n, val;
	char c;
	FILE *f;
	char fname[128];
	int opcode;
	REGISTER_SETTINGS_STRUCT *reg;

	reg = (REGISTER_SETTINGS_STRUCT *)*tag;

	len = parseOpPars(reg, address, tmp);
	if (!len)
		return;
	opcode = reg->oper;
	reg->bus = atoi(tmp[3]);
	/*
	if ((opcode == OPERATION_WRITE) || (opcode == OPERATION_READ) ||
		(opcode == OPERATION_WRITE_READ))
	{
		reg = createExtraRegister(reg, 0);
	}
	*/
	if(opcode != OPERATION_ACTIVATE_CH && opcode != OPERATION_DEACTIVATE_CH){
		reg->address = atoi(tmp[4]);
		reg->speed = GbtPortSpeeds[reg->gbtID];

		if (strcmp(tmp[5], "") == 0)
			reg->subAddress = -1;
		else
			reg->subAddress = atoi(tmp[5]);
		reg->size = atoi(tmp[6]);
		reg->i2ctype = 0;
		if(strcmp(tmp[7], ""))
			reg->i2ctype = atoi(tmp[7]);
		if(strcmp(tmp[8], ""))
			reg->i2cfreq = atoi(tmp[8]);
		else
			reg->i2cfreq = 3;
		if( len > 9)
			reg->sclMode = atoi(tmp[9]);
		else
			reg->sclMode = 0;
		if(len > 10)
		{
			strcpy(reg->fileName,tmp[10]);
			file_flag = 1;
		}
	}
	if(!file_flag)
	{
		data = &address[128];
		dataSize = (*size) - 128;
	}
	else
	{
		convertFname(reg->fileName, fname);
		gbtmsg(LOG_DEBUG, "file name %s (%s)",reg->fileName, fname);
		data = malloc(reg->size+1);
		p = data;
		dataSize = reg->size;
		f = fopen((const char *)&(fname), "r");
		if( f == NULL ){

			gbtmsg(LOG_ERR, ANSI_COLOR_RED "%s\n %s\n" ANSI_COLOR_RESET, fname, strerror(errno));
			reg->writingsStatus = BAD_FILE;
			dis_update_service(srvcI2CWriteID);
			goto end;
		}
		n = 0;
		while(!feof(f))
		{
			fscanf(f, "%x%c", &val, &c);
			*p = (char)val;
			p++;
			n++;
			if ( n >= dataSize)
				break;
		}
		fclose(f);
	}
	if (debugFlag != -1)
	{
		gbtmsg(LOG_DEBUG,"======================================\n");
		gbtmsg(LOG_DEBUG," gbtID <%d>\n", reg->gbtID);
		gbtmsg(LOG_DEBUG," scaID <%d>\n", reg->scaID);
		gbtmsg(LOG_DEBUG," bus <%d>\n", reg->bus);
		gbtmsg(LOG_DEBUG," address <%d>\n", reg->address);
		gbtmsg(LOG_DEBUG," subAddress <%d>\n", reg->subAddress);
		gbtmsg(LOG_DEBUG," I2C type <%d>\n", reg->i2ctype);
		gbtmsg(LOG_DEBUG," I2C Freq <%d>\n", reg->i2cfreq);
		gbtmsg(LOG_DEBUG," File Flag <%d>\n", file_flag);
		gbtmsg(LOG_DEBUG," size <%d>\n", reg->size);
		gbtmsg(LOG_DEBUG," data <");
		for(i = 0; i < reg->size; i++)
		{
			if (i < reg->size - 1)
				gbtmsg(LOG_DEBUG,"%02x ", data[i]);
			else
				gbtmsg(LOG_DEBUG,"%02x", data[i]);
		}
		gbtmsg(LOG_DEBUG,">\n");
		gbtmsg(LOG_DEBUG,"======================================\n");
	}

	switch(opcode)
	{
		case OPERATION_WRITE:		gbtmsg(LOG_DEBUG,"Command I2COperation <Write>");
											spawnCmndRegister(reg, data, dataSize, 2, srvcI2CWriteID);
//											I2CWriteReg(reg, data, dataSize, 1);
//											dis_update_service(srvcI2CWriteID);
											break;

		case OPERATION_READ:
gbtmsg(LOG_DEBUG,"Command I2COperation <Read>");
											spawnCmndRegister(reg, 0, 0, 3, srvcI2CReadID);
//											I2CReadReg(reg, 1);
//											dis_update_service(srvcI2CReadID);
											break;

		case OPERATION_WRITE_READ:	gbtmsg(LOG_DEBUG,"Command I2COperation <WriteRead>");
											spawnCmndRegister(reg, data, dataSize, 3, srvcI2CReadID);
											/*
											I2CWriteReg(reg, data, dataSize, 1);
											if (reg->writingsStatus == GbtSuccess)
												I2CReadReg(reg, 1);
											else
											{
												memset(reg->data, '\0', reg->size);
												reg->readingsStatus = reg->writingsStatus;
											}
											dis_update_service(srvcI2CReadID);
											*/
											break;
		case OPERATION_ACTIVATE_CH: gbtmsg(LOG_DEBUG,"Command I2COperation <ActivateChannel>");
										I2CSetChState(reg, 1, 1);
										dis_update_service(srvcI2CWriteID);
										break;
		case OPERATION_DEACTIVATE_CH: gbtmsg(LOG_DEBUG,"Command I2COperation <DeactivateChannel>");
									  I2CSetChState(reg, 0, 1);
									  dis_update_service(srvcI2CWriteID);
									  break;
		default:
			gbtmsg(LOG_DEBUG,"Command I2COperation <unknown operation>: %d",opcode);
	}

end:
	if(file_flag)
		free(data);

}
```

The takeaways are:
1. The ordering of the parameters:
    1. Operation mode
    2. GBT ID (translated by `configGetRealMasterId`, which is defined in `src/GbtCommon.c`)
    3. SCA ID
    4. I2C Bus
    5. GBT address
    6. GBT sub-address
    7. size
    8. I2C type
    9. I2C frequency
    10. SCL mode, default to 0
    11. filename

    The last two parameters are optional
