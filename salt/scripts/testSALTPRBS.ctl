// vim: ft=cs:
// Author: Mark Tobin

///////////////////
// Configuration //
///////////////////

string dpType = "SALTPRBS";
string dpName = "SaltPRBSTest";
string projName = "dist_1";


main() {
  DebugTN("SALT PRBS test initilization. Here we go!");

  if (!dpTypeExists(dpType)) {
    int status = createSaltPrbsDpType(dpType);
    DebugTN("Data point type "+dpType+" does not exist, creating one..."+status);
  }

  if (!dpExists(dpName)) {
    int status = createSaltPrbsDpInstance(dpType, dpName);
    DebugTN("Data point instance "+dpName+" does not exist, creating one..."+status);
  }

  dpConnect("runPRBSTest", "UTSLICETEST:SaltPRBSTest.test_is_running");
}


//////////////////////
// DP configuration //
//////////////////////

// Create data point type used for SALT PRBS test
int createSaltPrbsDpType(string dpType) {
  int status;
  dyn_dyn_string elements;
  dyn_dyn_int types;

  DebugTN("Making DP type: "+dpType);

  // Name of the elements.
  dynAppend(elements, makeDynString(dpType, ""));
  dynAppend(elements, makeDynString("", "nErrorsPerByte"));
  dynAppend(elements, makeDynString("", "secondsSinceStart"));
  dynAppend(elements, makeDynString("", "nFramesProcessed"));
  dynAppend(elements, makeDynString("", "test_is_running"));
  dynAppend(elements, makeDynString("", "checkByte"));
  dynAppend(elements, makeDynString("", "startTime"));
  dynAppend(elements, makeDynString("", "result"));

  // Data types.
  dynAppend(types, makeDynInt(DPEL_STRUCT));
  dynAppend(types, makeDynInt(0, DPEL_DYN_ULONG));
  dynAppend(types, makeDynInt(0, DPEL_ULONG));
  dynAppend(types, makeDynInt(0, DPEL_ULONG));
  dynAppend(types, makeDynInt(0, DPEL_BOOL));
  dynAppend(types, makeDynInt(0, DPEL_DYN_BOOL));
  dynAppend(types, makeDynInt(0, DPEL_FLOAT));
  dynAppend(types, makeDynInt(0, DPEL_STRING));

  status = dpTypeCreate(elements, types);
  return status;
}

// Create data point instance
int createSaltPrbsDpInstance(string dpType, string dpName) {
  int status;

  DebugTN("Making DP type: "+dpType+", DP instance: "+dpName);

  status = dpCreate(dpName, dpType);
  return status;
}


//
// Generate the next value of the Salt pseudo-random sequence 0
//
char NextValue(char CVal) {
  bool ornot = 0;
  for (int mask = 1; mask != 0x80; mask <<= 1) {
    ornot |= (CVal & mask);
  }
  ornot = !ornot;
  bool xorornot = ((CVal & 0x80) >> 7) ^ ornot;
  bool feedback = xorornot ^ ((CVal & 0x08) >> 3) ^ ((CVal & 0x10) >> 4) ^
                  ((CVal & 0x20) >> 5);
  char NValue = (CVal << 1) | feedback;
  return NValue;
}

//
// Call back function to start running PRBS test
//
void runPRBSTest(string dpe, bool value) {
  DebugTN("runTest", dpe, value, dpSubStr(dpe, DPSUB_DP));
  if (value) { // start the test
    // reset the counters
    float startTime = timeToInterval(getCurrentTime());
    ulong secondsSinceStart = 0;
    ulong numberOfFramesProcessed = 0;
    dyn_ulong numberOfErrorsPerByte = makeDynULong();
    numberOfErrorsPerByte[12] = 0;
    dpSet("UTSLICETEST:SaltPRBSTest.startTime", startTime);
    dpSet("UTSLICETEST:SaltPRBSTest.secondsSinceStart", secondsSinceStart);
    dpSet("UTSLICETEST:SaltPRBSTest.nFramesProcessed", numberOfFramesProcessed);
    dpSet("UTSLICETEST:SaltPRBSTest.nErrorsPerByte", numberOfErrorsPerByte);
    DebugTN(__FUNCTION__);
    DebugTN("StartTime:", startTime, secondsSinceStart);
    DebugTN("Reset counters", strjoin(numberOfErrorsPerByte, "|"));
    dpConnect(
        "EP_updatePRBSTest",
        "UTSLICETEST:TELL40_Dev1_1.top_tell40_monitoring.memory.readings");
    //    dpConnect( "EP_updatePRBSTest",
    //    "UTSLICETEST:TELL40_Dev1_0.top_tell40_monitoring.memory.readings" );
  } else {
    if (dpDisconnect("EP_updatePRBSTest",
                     "UTSLICETEST:TELL40_Dev1_1.top_tell40_monitoring.memory."
                     "readings") == -1) {
      //    if( dpDisconnect( "EP_updatePRBSTest",
      //    "UTSLICETEST:TELL40_Dev1_0.top_tell40_monitoring.memory.readings" )
      //    == -1 ) {
      DebugTN("Data point was probably not connected");
    }
  }
}

//
// Call back function when reading memory from Tell40
//
void EP_updatePRBSTest(string dp, dyn_char readings) {

  float startTime;
  ulong secondsSinceStart;
  ulong numberOfFramesProcessed;
  dyn_ulong numberOfErrorsPerByte;
  dyn_bool checkByte;
  dpGet("UTSLICETEST:SaltPRBSTest.startTime", startTime);
  dpGet("UTSLICETEST:SaltPRBSTest.secondsSinceStart", secondsSinceStart);
  dpGet("UTSLICETEST:SaltPRBSTest.nFramesProcessed", numberOfFramesProcessed);
  dpGet("UTSLICETEST:SaltPRBSTest.nErrorsPerByte", numberOfErrorsPerByte);
  dpGet("UTSLICETEST:SaltPRBSTest.checkByte", checkByte);

  string aux = fwGbt_convertByteToHex(readings);
  //   DebugTN( dynlen(readings), strlen(aux), aux );
  dyn_dyn_char data;
  data[12] = makeDynChar();
  int firstCheckedByte = -1;
  for (int i = 0; i < strlen(aux); i = i + 32) {
    //        DebugTN( substr(aux, i+24, 8), substr(aux, i+16, 8), substr(aux,
    //        i+8, 8), substr(aux, i, 8));
    // salt asic data on bytes 0 to 11 only... the first 4-bytes are probably
    // the GBT header...
    string elinkData =
        strjoin(makeDynString(substr(aux, i + 16, 8), substr(aux, i + 8, 8),
                              substr(aux, i, 8)),
                "");
    //     DebugTN( elinkData );
    dyn_char myData = fwGbt_convertHexToByte(elinkData);
    //     DebugTN( dynlen(myData), myData );
    // select interesting columns
    for (int iByte = 1; iByte <= 12; iByte++) {
      if (checkByte[iByte]) {
        dynAppend(data[iByte], myData[iByte]);
        if (firstCheckedByte < 0) {
          firstCheckedByte = iByte;
        }
      }
    }
  }
  //   DebugTN( data );
  // check PRBS for each byte
  for (int iByte = 1; iByte <= dynlen(data); iByte++) {
    for (int iCycle = 2; iCycle <= dynlen(data[iByte]); iCycle++) {
      char expectedValue = NextValue(data[iByte][iCycle - 1]);
      if (data[iByte][iCycle] != expectedValue) {
        if (numberOfErrorsPerByte[iByte] < 100) {
          DebugTN("Error on byte " + iByte + " and cycle " + iCycle,
                  data[iByte][iCycle], data[iByte][iCycle - 1], expectedValue);
          if (numberOfErrorsPerByte[iByte] < 5) {
            DebugTN(aux);
          }
          DebugTN("Error on byte " + iByte + " and cycle " + iCycle,
                  data[iByte][iCycle], data[iByte][iCycle - 1], expectedValue);
        }
        numberOfErrorsPerByte[iByte] += 1;
      }
      if (iByte == firstCheckedByte) {
        numberOfFramesProcessed += 1;
      }
    }
  }
  // update text field...
  time t = getCurrentTime();
  ulong secondsSinceStart = (ulong)(timeToInterval(t) - startTime);
  string status = "";
  status = secondsSinceStart + "s | " + numberOfFramesProcessed + " | " +
           strjoin(numberOfErrorsPerByte, "-");
  //   DebugTN( status );
  //   TEXT_FIELD_status.text( status );
  //   TEXT_FIELD_status.text( (status + "|  Errors | " + strjoin(
  //   numberOfErrorsPerByte, "|" )) );
  dpSet("UTSLICETEST:SaltPRBSTest.secondsSinceStart", secondsSinceStart);
  dpSet("UTSLICETEST:SaltPRBSTest.nFramesProcessed", numberOfFramesProcessed);
  dpSet("UTSLICETEST:SaltPRBSTest.nErrorsPerByte", numberOfErrorsPerByte);
  dpSet("UTSLICETEST:SaltPRBSTest.result", status);
}
