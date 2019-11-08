// vim: ft=cs:
// Author: Mark Tobin
// Last Change: Thu Nov 07, 2019 at 07:54 PM -0500

#uses "wizardFramework.ctl"

///////////////////
// Configuration //
///////////////////

const string dpType = "SALTPRBS";
const string dpName = "SaltPRBSTest";
const string projName = "dist_1";
const string tell40Name = "TELL40_Dev1_1";

main() {
  DebugTN("SALT PRBS test initilization. Here we go!");

  if (!dpTypeExists(dpType)) {
    int status = createSaltPrbsDpType(dpType);
    DebugTN("Data point type " + dpType + " does not exist, creating one..." +
            status);
  }

  if (!dpExists(dpName)) {
    int status = createSaltPrbsDpInstance(dpType, dpName);
    DebugTN("Data point instance " + dpName +
            " does not exist, creating one..." + status);
  }

  dpConnect("runSaltPrbsTest", projName + ":SaltPRBSTest.test_is_running");
}

//////////////////////
// DP configuration //
//////////////////////

// Create data point type used for SALT PRBS test.
int createSaltPrbsDpType(string dpType) {
  int status;
  dyn_dyn_string elements;
  dyn_dyn_int types;

  DebugTN("Making DP type: " + dpType);

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
  dynAppend(types, makeDynInt(0, DPEL_DYN_CHAR));

  status = dpTypeCreate(elements, types);
  return status;
}

// Create data point instances.
int createSaltPrbsDpInstance(string dpType, string dpName) {
  int status;

  DebugTN("Making DP type: " + dpType + ", DP instance: " + dpName);

  status = dpCreate(dpName, dpType);
  return status;
}

//////////
// PRBS //
//////////

// Generate the next value of the SALT pseudo-random sequence 0.
char nextPrbsValue(char cVal) {
  bool ornot = 0;

  for (int mask = 1; mask != 0x80; mask <<= 1) {
    ornot |= (cVal & mask);
  }

  ornot = !ornot;

  bool xorornot = ((cVal & 0x80) >> 7) ^ ornot;
  bool feedback = xorornot ^ ((cVal & 0x08) >> 3) ^ ((cVal & 0x10) >> 4) ^
                  ((cVal & 0x20) >> 5);

  char nVal = (cVal << 1) | feedback;
  return nVal;
}

/////////////////////////
// Call back functions //
/////////////////////////

// Call back function to start running PRBS test.
void runSaltPrbsTest(string dpe, bool testIsRunning) {
  DebugTN("runTest" + dpe + testIsRunning + dpSubStr(dpe, DPSUB_DP));
  if (testIsRunning) {
    // Reset the counters
    float startTime = timeToInterval(getCurrentTime());
    ulong secondsSinceStart = 0;
    ulong numberOfFramesProcessed = 0;
    dyn_ulong numberOfErrorsPerByte = makeDynULong();
    numberOfErrorsPerByte[12] = 0;

    dpSet(projName + ":SaltPRBSTest.startTime", startTime);
    dpSet(projName + ":SaltPRBSTest.secondsSinceStart", secondsSinceStart);
    dpSet(projName + ":SaltPRBSTest.nFramesProcessed", numberOfFramesProcessed);
    dpSet(projName + ":SaltPRBSTest.nErrorsPerByte", numberOfErrorsPerByte);

    DebugTN(__FUNCTION__);
    DebugTN("StartTime:", startTime, secondsSinceStart);
    DebugTN("Reset counters", strjoin(numberOfErrorsPerByte, "|"));

    dpConnect("updateSaltPrbsTest",
              projName + ":" + tell40Name +
                  ".top_tell40_monitoring.memory.readings");

  } else {
    if (dpDisconnect("updateSaltPrbsTest", projName + ":" + tell40Name +
                                               ".top_tell40_monitoring.memory."
                                               "readings") == -1) {
      DebugTN("Data point was probably not connected");
    }
  }
}

// Call back function when reading memory from TELL40.
void updateSaltPrbsTest(string dp, dyn_char readings) {
  float startTime;
  ulong secondsSinceStart;
  ulong numberOfFramesProcessed;
  dyn_ulong numberOfErrorsPerByte;
  dyn_bool checkByte;

  dpGet(projName + ":SaltPRBSTest.startTime", startTime);
  dpGet(projName + ":SaltPRBSTest.secondsSinceStart", secondsSinceStart);
  dpGet(projName + ":SaltPRBSTest.nFramesProcessed", numberOfFramesProcessed);
  dpGet(projName + ":SaltPRBSTest.nErrorsPerByte", numberOfErrorsPerByte);
  dpGet(projName + ":SaltPRBSTest.checkByte", checkByte);

  dyn_char data;

  string aux = fwGbt_convertByteToHex(readings);
  for (int i = 0; i < strlen(aux); i = i + 32) {
    // SALT ASIC data on bytes 0 to 11 only... the first 4-bytes are probably
    // the GBT header...
    string elinkData =
        strjoin(makeDynString(substr(aux, i + 16, 8), substr(aux, i + 8, 8),
                              substr(aux, i, 8)),
                "");
    dyn_char myData = fwGbt_convertHexToByte(elinkData);
    // Keep all elink data.
    dynAppend(data, myData);
  }


  // Check PRBS for each byte.
  for (int iCycle = 2; iCycle <= dynlen(data); iCycle++) {
    // Update total number of processed frames.
    numberOfFramesProcessed += 1;

    for (int iByte = 1; iByte <= dynlen(data[iCycle]); iByte++) {
      if (checkByte[iByte]) { // Only check ticked bytes.
        char currentVal = data[iCycle][iByte];
        char previousVal = data[iCycle - 1][iByte];
        char expectedVal = nextPrbsValue(previousVal);

        if (data[iByte][iCycle] != expectedValue) {
          DebugTN("Error on byte " + iByte + " and cycle " + iCycle,
                  data[iByte][iCycle], data[iByte][iCycle - 1], expectedValue);
          numberOfErrorsPerByte[iByte] += 1;
        }
      }
    }
  }

  // Update text fields.
  time t = getCurrentTime();
  ulong secondsSinceStart = (ulong)(timeToInterval(t) - startTime);
  string status = "";
  status = secondsSinceStart + "s | " + numberOfFramesProcessed + " | " +
           strjoin(numberOfErrorsPerByte, "-");

  dpSet(projName + ":SaltPRBSTest.secondsSinceStart", secondsSinceStart);
  dpSet(projName + ":SaltPRBSTest.nFramesProcessed", numberOfFramesProcessed);
  dpSet(projName + ":SaltPRBSTest.nErrorsPerByte", numberOfErrorsPerByte);
  dpSet(projName + ":SaltPRBSTest.result", status);
}
