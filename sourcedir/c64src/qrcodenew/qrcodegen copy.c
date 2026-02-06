
#include <conio.h>
#include <stdio.h>
#include <stdlib.h>
#include <peekpoke.h>
#include <string.h>
#include <c64.h>
#include <cbm_petscii_charmap.h>
#include <conio.h>
#include <assert.h>
#include <limits.h>
#include <stdlib.h>
#include <string.h>
#include "qrcodegen.h"

#ifndef QRCODEGEN_TEST
	#define testable static  // Keep functions private
#else
	#define testable  // Expose private functions
#endif


/*---- Forward declarations for private functions ----*/

// Regarding all public and private functions defined in this source file:
// - They require all pointer/array arguments to be not null unless the array length is zero.
// - They only read input scalar/array arguments, write to output pointer/array
//   arguments, and return scalar values; they are "pure" functions.
// - They don't read mutable global variables or write to any global variables.
// - They don't perform I/O, read the clock, print to console, etc.
// - They allocate a small and constant amount of stack memory.
// - They don't allocate or free any memory on the heap.
// - They don't recurse or mutually recurse. All the code
//   could be inlined into the top-level public functions.
// - They run in at most quadratic time with respect to input arguments.
//   Most functions run in linear time, and some in constant time.
//   There are no unbounded loops or non-obvious termination conditions.
// - They are completely thread-safe if the caller does not give the
//   same writable buffer to concurrent calls to these functions.

testable void appendBitsToBuffer(unsigned int val, int numBits, uint8_t buffer[], int *bitLen);

testable void addEccAndInterleave(uint8_t data[], int version, enum qrcodegen_Ecc ecl, uint8_t result[]);
testable int getNumDataCodewords(int version, enum qrcodegen_Ecc ecl);
testable int getNumRawDataModules(int ver);

testable void reedSolomonComputeDivisor(int degree, uint8_t result[]);
testable void reedSolomonComputeRemainder(const uint8_t data[], int dataLen,
	const uint8_t generator[], int degree, uint8_t result[]);
testable uint8_t reedSolomonMultiply(uint8_t x, uint8_t y);

testable void initializeFunctionModules(int version, uint8_t qrcode[]);
static void drawLightFunctionModules(uint8_t qrcode[], int version);
static void drawFormatBits(enum qrcodegen_Ecc ecl, enum qrcodegen_Mask mask, uint8_t qrcode[]);
testable int getAlignmentPatternPositions(int version, uint8_t result[7]);
static void fillRectangle(int left, int top, int width, int height, uint8_t qrcode[]);

static void drawCodewords(const uint8_t data[], int dataLen, uint8_t qrcode[]);
static void applyMask(const uint8_t functionModules[], uint8_t qrcode[], enum qrcodegen_Mask mask);
static long getPenaltyScore(const uint8_t qrcode[]);
static int finderPenaltyCountPatterns(const int runHistory[7], int qrsize);
static int finderPenaltyTerminateAndCount(bool currentRunColor, int currentRunLength, int runHistory[7], int qrsize);
static void finderPenaltyAddHistory(int currentRunLength, int runHistory[7], int qrsize);

testable bool getModuleBounded(const uint8_t qrcode[], int x, int y);
testable void setModuleBounded(uint8_t qrcode[], int x, int y, bool isDark);
testable void setModuleUnbounded(uint8_t qrcode[], int x, int y, bool isDark);
static bool getBit(int x, int i);

testable int calcSegmentBitLength(enum qrcodegen_Mode mode, size_t numChars);
testable int getTotalBits(const struct qrcodegen_Segment segs[], size_t len, int version);
static int numCharCountBits(enum qrcodegen_Mode mode, int version);



/*---- Private tables of constants ----*/

// The set of all legal characters in alphanumeric mode, where each character
// value maps to the index in the string. For checking text and encoding segments.
static const char *ALPHANUMERIC_CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:";

// Sentinel value for use in only some functions.
#define LENGTH_OVERFLOW -1

// For generating error correction codes.
testable const int8_t ECC_CODEWORDS_PER_BLOCK[4][41] = {
	// Version: (note that index 0 is for padding, and is set to an illegal value)
	//0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40    Error correction level
	{-1,  7, 10, 15, 20, 26, 18, 20, 24, 30, 18, 20, 24, 26, 30, 22, 24, 28, 30, 28, 28, 28, 28, 30, 30, 26, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30},  // Low
	{-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26, 30, 22, 22, 24, 24, 28, 28, 26, 26, 26, 26, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28},  // Medium
	{-1, 13, 22, 18, 26, 18, 24, 18, 22, 20, 24, 28, 26, 24, 20, 30, 24, 28, 28, 26, 30, 28, 30, 30, 30, 30, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30},  // Quartile
	{-1, 17, 28, 22, 16, 22, 28, 26, 26, 24, 28, 24, 28, 22, 24, 24, 30, 28, 28, 26, 28, 30, 24, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30},  // High
};

#define qrcodegen_REED_SOLOMON_DEGREE_MAX 30  // Based on the table above

// For generating error correction codes.
testable const int8_t NUM_ERROR_CORRECTION_BLOCKS[4][41] = {
	// Version: (note that index 0 is for padding, and is set to an illegal value)
	//0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40    Error correction level
	{-1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 4,  4,  4,  4,  4,  6,  6,  6,  6,  7,  8,  8,  9,  9, 10, 12, 12, 12, 13, 14, 15, 16, 17, 18, 19, 19, 20, 21, 22, 24, 25},  // Low
	{-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5,  5,  8,  9,  9, 10, 10, 11, 13, 14, 16, 17, 17, 18, 20, 21, 23, 25, 26, 28, 29, 31, 33, 35, 37, 38, 40, 43, 45, 47, 49},  // Medium
	{-1, 1, 1, 2, 2, 4, 4, 6, 6, 8, 8,  8, 10, 12, 16, 12, 17, 16, 18, 21, 20, 23, 23, 25, 27, 29, 34, 34, 35, 38, 40, 43, 45, 48, 51, 53, 56, 59, 62, 65, 68},  // Quartile
	{-1, 1, 1, 2, 4, 4, 4, 5, 6, 8, 8, 11, 11, 16, 16, 18, 16, 19, 21, 25, 25, 25, 34, 30, 32, 35, 37, 40, 42, 45, 48, 51, 54, 57, 60, 63, 66, 70, 74, 77, 81},  // High
};

// For automatic mask pattern selection.
static const int PENALTY_N1 =  3;
static const int PENALTY_N2 =  3;
static const int PENALTY_N3 = 40;
static const int PENALTY_N4 = 10;



/*---- High-level QR Code encoding functions ----*/

// Public function - see documentation comment in header file.
bool qrcodegen_encodeText(const char *text, uint8_t tempBuffer[], uint8_t qrcode[],
    enum qrcodegen_Ecc ecl, int minVersion, int maxVersion, enum qrcodegen_Mask mask, bool boostEcl) {
    
    size_t textLen;
    size_t bufLen;
    struct qrcodegen_Segment seg;

    textLen = strlen(text);
    if (textLen == 0) {
        return qrcodegen_encodeSegmentsAdvanced(NULL, 0, ecl, minVersion, maxVersion, mask, boostEcl, tempBuffer, qrcode);
    }
    
    bufLen = (size_t)qrcodegen_BUFFER_LEN_FOR_VERSION(maxVersion);
    
    if (qrcodegen_isNumeric(text)) {
        if (qrcodegen_calcSegmentBufferSize(qrcodegen_Mode_NUMERIC, textLen) > bufLen) {
            goto fail;
        }
        /* Fixed: Passing &seg as the 3rd argument */
        qrcodegen_makeNumeric(text, tempBuffer, &seg);
    } else if (qrcodegen_isAlphanumeric(text)) {
        if (qrcodegen_calcSegmentBufferSize(qrcodegen_Mode_ALPHANUMERIC, textLen) > bufLen) {
            goto fail;
        }
        /* Fixed: Passing &seg as the 3rd argument */
        qrcodegen_makeAlphanumeric(text, tempBuffer, &seg);
    } else {
        if (qrcodegen_calcSegmentBufferSize(qrcodegen_Mode_BYTE, textLen) > bufLen) {
            goto fail;
        }
        /* Fixed: Passing &seg as the 4th argument (based on the prototype) */
        qrcodegen_makeBytes((const uint8_t *)text, textLen, tempBuffer, &seg);
    }
    
    return qrcodegen_encodeSegmentsAdvanced(&seg, 1, ecl, minVersion, maxVersion, mask, boostEcl, tempBuffer, qrcode);

fail:
    return false;
}


// Public function - see documentation comment in header file.
bool qrcodegen_encodeBinary(uint8_t dataAndTemp[], size_t dataLen, uint8_t qrcode[],
		enum qrcodegen_Ecc ecl, int minVersion, int maxVersion, enum qrcodegen_Mask mask, bool boostEcl) {
	
	struct qrcodegen_Segment seg;
	seg.mode = qrcodegen_Mode_BYTE;
	seg.bitLength = calcSegmentBitLength(seg.mode, dataLen);
	if (seg.bitLength == LENGTH_OVERFLOW) {
		qrcode[0] = 0;  // Set size to invalid value for safety
		return false;
	}
	seg.numChars = (int)dataLen;
	seg.data = dataAndTemp;
	return qrcodegen_encodeSegmentsAdvanced(&seg, 1, ecl, minVersion, maxVersion, mask, boostEcl, dataAndTemp, qrcode);
}


// Appends the given number of low-order bits of the given value to the given byte-based
// bit buffer, increasing the bit length. Requires 0 <= numBits <= 16 and val < 2^numBits.
testable void appendBitsToBuffer(unsigned int val, int numBits, uint8_t buffer[], int *bitLen) {
    int i;
    for (i = numBits - 1; i >= 0; i--) {
        buffer[*bitLen >> 3] |= ((val >> i) & 1) << (7 - (*bitLen & 7));
        (*bitLen)++;
    }
}



/*---- Low-level QR Code encoding functions ----*/

// Public function - see documentation comment in header file.
bool qrcodegen_encodeSegments(const struct qrcodegen_Segment segs[], size_t len,
		enum qrcodegen_Ecc ecl, uint8_t tempBuffer[], uint8_t qrcode[]) {
	return qrcodegen_encodeSegmentsAdvanced(segs, len, ecl,
		qrcodegen_VERSION_MIN, qrcodegen_VERSION_MAX, qrcodegen_Mask_AUTO, true, tempBuffer, qrcode);
}


// Public function - see documentation comment in header file.
bool qrcodegen_encodeSegmentsAdvanced(const struct qrcodegen_Segment segs[], size_t len, enum qrcodegen_Ecc ecl,
                                        int minVersion, int maxVersion, enum qrcodegen_Mask mask, bool boostEcl, uint8_t tempBuffer[], uint8_t qrcode[]) {
    int version;
    int dataUsedBits;
    int dataCapacityBits;
    int i;
    int j;
    int bitLen;
    int terminatorBits;
    int bit;
    size_t si;
    uint8_t padByte;
    long minPenalty;
    long penalty;
    const struct qrcodegen_Segment *seg;
    enum qrcodegen_Mask msk;

    assert(segs != NULL || len == 0);
    assert(qrcodegen_VERSION_MIN <= minVersion && minVersion <= maxVersion && maxVersion <= qrcodegen_VERSION_MAX);
    assert(0 <= (int)ecl && (int)ecl <= 3 && -1 <= (int)mask && (int)mask <= 7);

    for (version = minVersion; ; version++) {
        dataCapacityBits = getNumDataCodewords(version, ecl) * 8;
        dataUsedBits = getTotalBits(segs, len, version);
        if (dataUsedBits != -1 && dataUsedBits <= dataCapacityBits) {
            break;
        }
        if (version >= maxVersion) {
            qrcode[0] = 0;
            return false;
        }
    }
    assert(dataUsedBits != -1);

    for (i = (int)qrcodegen_Ecc_MEDIUM; i <= (int)qrcodegen_Ecc_HIGH; i++) {
        if (boostEcl && dataUsedBits <= getNumDataCodewords(version, (enum qrcodegen_Ecc)i) * 8) {
            ecl = (enum qrcodegen_Ecc)i;
        }
    }

    memset(qrcode, 0, (size_t)qrcodegen_BUFFER_LEN_FOR_VERSION(version) * sizeof(qrcode[0]));
    bitLen = 0;
    for (si = 0; si < len; si++) {
        seg = &segs[si];
        appendBitsToBuffer((unsigned int)seg->mode, 4, qrcode, &bitLen);
        appendBitsToBuffer((unsigned int)seg->numChars, numCharCountBits(seg->mode, version), qrcode, &bitLen);
        for (j = 0; j < seg->bitLength; j++) {
            bit = (seg->data[j >> 3] >> (7 - (j & 7))) & 1;
            appendBitsToBuffer((unsigned int)bit, 1, qrcode, &bitLen);
        }
    }
    assert(bitLen == dataUsedBits);

    dataCapacityBits = getNumDataCodewords(version, ecl) * 8;
    assert(bitLen <= dataCapacityBits);
    terminatorBits = dataCapacityBits - bitLen;
    if (terminatorBits > 4) {
        terminatorBits = 4;
    }
    appendBitsToBuffer(0, terminatorBits, qrcode, &bitLen);
    appendBitsToBuffer(0, (8 - bitLen % 8) % 8, qrcode, &bitLen);
    assert(bitLen % 8 == 0);

    for (padByte = 0xEC; bitLen < dataCapacityBits; padByte ^= 0xEC ^ 0x11) {
        appendBitsToBuffer(padByte, 8, qrcode, &bitLen);
    }

    addEccAndInterleave(qrcode, version, ecl, tempBuffer);
    initializeFunctionModules(version, qrcode);
    drawCodewords(tempBuffer, getNumRawDataModules(version) / 8, qrcode);
    drawLightFunctionModules(qrcode, version);
    initializeFunctionModules(version, tempBuffer);

    if (mask == qrcodegen_Mask_AUTO) {
        minPenalty = 2147483647L;
        for (i = 0; i < 8; i++) {
            msk = (enum qrcodegen_Mask)i;
            applyMask(tempBuffer, qrcode, msk);
            drawFormatBits(ecl, msk, qrcode);
            penalty = getPenaltyScore(qrcode);
            if (penalty < minPenalty) {
                mask = msk;
                minPenalty = penalty;
            }
            applyMask(tempBuffer, qrcode, msk);
        }
    }
    assert(0 <= (int)mask && (int)mask <= 7);
    applyMask(tempBuffer, qrcode, mask);
    drawFormatBits(ecl, mask, qrcode);
    return true;
}



/*---- Error correction code generation functions ----*/

// Appends error correction bytes to each block of the given data array, then interleaves
// bytes from the blocks and stores them in the result array. data[0 : dataLen] contains
// the input data. data[dataLen : rawCodewords] is used as a temporary work area and will
// be clobbered by this function. The final answer is stored in result[0 : rawCodewords].
void addEccAndInterleave(uint8_t data[], int version, int ecl, uint8_t result[]) {
    static uint8_t i, j;
    static uint8_t numBlocks;
    static uint8_t blockEccLen;
    static uint16_t dataLen;
    static uint8_t numShortBlocks;
    static uint8_t shortBlockDataLen;
    static uint8_t currentDatLen;
    static uint16_t k;
    
    static uint8_t *dat;
    static uint8_t *ecc;
    static uint8_t rsdiv[32];

    numBlocks = NUM_BLOCKS_TABLE[ecl][version];
    blockEccLen = ECC_LEN_TABLE[ecl][version];
    dataLen = DATA_LEN_TABLE[ecl][version];
    
    numShortBlocks = NUM_SHORT_BLOCKS_TABLE[ecl][version];
    shortBlockDataLen = SHORT_BLOCK_LEN_TABLE[ecl][version];

    reedSolomonComputeDivisor(blockEccLen, rsdiv);
    dat = data;

    for (i = 0; i < numBlocks; i++) {
        currentDatLen = shortBlockDataLen;
        if (i >= numShortBlocks) {
            currentDatLen++;
        }
        
        ecc = &data[dataLen];
        reedSolomonComputeRemainder(dat, currentDatLen, rsdiv, blockEccLen, ecc);

        k = (uint16_t)i;
        for (j = 0; j < currentDatLen; j++) {
            if (j == shortBlockDataLen) {
                k -= numShortBlocks;
            }
            result[k] = dat[j];
            k += numBlocks;
        }

        k = dataLen + i;
        for (j = 0; j < blockEccLen; j++) {
            result[k] = ecc[j];
            k += numBlocks;
        }
        dat += currentDatLen;
    }
}


// Returns the number of 8-bit codewords that can be used for storing data (not ECC),
// for the given version number and error correction level. The result is in the range [9, 2956].
testable int getNumDataCodewords(int version, enum qrcodegen_Ecc ecl) {
	int v = version, e = (int)ecl;
	assert(0 <= e && e < 4);
	return getNumRawDataModules(v) / 8
		- ECC_CODEWORDS_PER_BLOCK    [e][v]
		* NUM_ERROR_CORRECTION_BLOCKS[e][v];
}


// Returns the number of data bits that can be stored in a QR Code of the given version number, after
// all function modules are excluded. This includes remainder bits, so it might not be a multiple of 8.
// The result is in the range [208, 29648]. This could be implemented as a 40-entry lookup table.
testable int getNumRawDataModules(int ver) {
  int result, numAlign;
	assert(qrcodegen_VERSION_MIN <= ver && ver <= qrcodegen_VERSION_MAX);
	result = (16 * ver + 128) * ver + 64;
	if (ver >= 2) {
		numAlign = ver / 7 + 2;
		result -= (25 * numAlign - 10) * numAlign - 55;
		if (ver >= 7)
			result -= 36;
	}
	assert(208 <= result && result <= 29648);
	return result;
}



/* Standard GF(2^8) tables for QR (Polynomial 0x11D) */
extern const uint8_t GF_EXP[512]; /* 512 to avoid modulo 255 during addition */
extern const uint8_t GF_LOG[256];

/* Faster macro for 6502 C compilers */
#define GF_MUL(a, b) ((a && b) ? GF_EXP[GF_LOG[a] + GF_LOG[b]] : 0)


/*---- Reed-Solomon ECC generator functions ----*/

// Computes a Reed-Solomon ECC generator polynomial for the given degree, storing in result[0 : degree].
// This could be implemented as a lookup table over all possible parameter values, instead of as an algorithm.
testable void reedSolomonComputeDivisor(int degree, uint8_t result[]) {
  int i, j;
  uint8_t root;
	assert(1 <= degree && degree <= qrcodegen_REED_SOLOMON_DEGREE_MAX);
	// Polynomial coefficients are stored from highest to lowest power, excluding the leading term which is always 1.
	// For example the polynomial x^3 + 255x^2 + 8x + 93 is stored as the uint8 array {255, 8, 93}.
	memset(result, 0, (size_t)degree * sizeof(result[0]));
	result[degree - 1] = 1;  // Start off with the monomial x^0
	
	// Compute the product polynomial (x - r^0) * (x - r^1) * (x - r^2) * ... * (x - r^{degree-1}),
	// drop the highest monomial term which is always 1x^degree.
	// Note that r = 0x02, which is a generator element of this field GF(2^8/0x11D).
	root = 1;
	for (i = 0; i < degree; i++) {
		// Multiply the current product by (x - r^i)
		for (j = 0; j < degree; j++) {
			result[j] = reedSolomonMultiply(result[j], root);
			if (j + 1 < degree)
				result[j] ^= result[j + 1];
		}
		root = reedSolomonMultiply(root, 0x02);
	}
}


// Computes the Reed-Solomon error correction codeword for the given data and divisor polynomials.
// The remainder when data[0 : dataLen] is divided by divisor[0 : degree] is stored in result[0 : degree].
// All polynomials are in big endian, and the generator has an implicit leading1 term.
testable void reedSolomonComputeRemainder(const uint8_t data[], int dataLen,
        const uint8_t generator[], int degree, uint8_t result[])
{
    int i;
    int j;
    uint8_t factor;

    assert(1 <= degree && degree <= qrcodegen_REED_SOLOMON_DEGREE_MAX);
    memset(result, 0, (size_t)degree * sizeof(result[0]));

    for (i = 0; i < dataLen; i++) {
        factor = data[i] ^ result[0];
        memmove(&result[0], &result[1], (size_t)(degree - 1) * sizeof(result[0]));
        result[degree - 1] = 0;
        for (j = 0; j < degree; j++)
            result[j] ^= reedSolomonMultiply(generator[j], factor);
    }
}


#undef qrcodegen_REED_SOLOMON_DEGREE_MAX


// Returns the product of the two given field elements modulo GF(2^8/0x11D).
// All inputs are valid. This could be implemented as a 256*256 lookup table.
testable uint8_t reedSolomonMultiply(uint8_t x, uint8_t y)
{
    uint8_t z;
    int i;

    z = 0;
    for (i = 7; i >= 0; i--) {
        z = (uint8_t)((z << 1) ^ ((z >> 7) * 0x11D));
        z ^= ((y >> i) & 1) * x;
    }
    return z;
}




/*---- Drawing function modules ----*/

// Clears the given QR Code grid with light modules for the given
// version's size, then marks every function module as dark.
testable void initializeFunctionModules(int version, uint8_t qrcode[]) {
    int qrsize;
    int numAlign;
    int i;
    int j;
    uint8_t alignPatPos[7];

    qrsize = version * 4 + 17;
    memset(qrcode, 0, (size_t)((qrsize * qrsize + 7) / 8 + 1) * sizeof(qrcode[0]));
    qrcode[0] = (uint8_t)qrsize;

    fillRectangle(6, 0, 1, qrsize, qrcode);
    fillRectangle(0, 6, qrsize, 1, qrcode);

    fillRectangle(0, 0, 9, 9, qrcode);
    fillRectangle(qrsize - 8, 0, 8, 9, qrcode);
    fillRectangle(0, qrsize - 8, 9, 8, qrcode);

    numAlign = getAlignmentPatternPositions(version, alignPatPos);
    for (i = 0; i < numAlign; i++) {
        for (j = 0; j < numAlign; j++) {
            if (!((i == 0 && j == 0) || (i == 0 && j == numAlign - 1) || (i == numAlign - 1 && j == 0))) {
                fillRectangle(alignPatPos[i] - 2, alignPatPos[j] - 2, 5, 5, qrcode);
            }
        }
    }

    if (version >= 7) {
        fillRectangle(qrsize - 11, 0, 3, 6, qrcode);
        fillRectangle(0, qrsize - 11, 6, 3, qrcode);
    }
}


// Draws light function modules and possibly some dark modules onto the given QR Code, without changing
// non-function modules. This does not draw the format bits. This requires all function modules to be previously
// marked dark (namely by initializeFunctionModules()), because this may skip redrawing dark function modules.
static void drawLightFunctionModules(uint8_t qrcode[], int version) {
    int qrsize;
    int i;
    int j;
    int k;
    int dx;
    int dy;
    int dist;
    int numAlign;
    int rem;
    long bits;
    uint8_t alignPatPos[7];

    qrsize = qrcodegen_getSize(qrcode);

    for (i = 7; i < qrsize - 7; i += 2) {
        setModuleBounded(qrcode, 6, i, 0);
        setModuleBounded(qrcode, i, 6, 0);
    }

    for (dy = -4; dy <= 4; dy++) {
        for (dx = -4; dx <= 4; dx++) {
            dist = abs(dx);
            if (abs(dy) > dist) {
                dist = abs(dy);
            }
            if (dist == 2 || dist == 4) {
                setModuleUnbounded(qrcode, 3 + dx, 3 + dy, 0);
                setModuleUnbounded(qrcode, qrsize - 4 + dx, 3 + dy, 0);
                setModuleUnbounded(qrcode, 3 + dx, qrsize - 4 + dy, 0);
            }
        }
    }

    numAlign = getAlignmentPatternPositions(version, alignPatPos);
    for (i = 0; i < numAlign; i++) {
        for (j = 0; j < numAlign; j++) {
            if ((i == 0 && j == 0) || (i == 0 && j == numAlign - 1) || (i == numAlign - 1 && j == 0)) {
                continue;
            }
            for (dy = -1; dy <= 1; dy++) {
                for (dx = -1; dx <= 1; dx++) {
                    setModuleBounded(qrcode, alignPatPos[i] + dx, alignPatPos[j] + dy, (dx == 0 && dy == 0));
                }
            }
        }
    }

    if (version >= 7) {
        rem = version;
        for (i = 0; i < 12; i++) {
            rem = (rem << 1) ^ ((rem >> 11) * 0x1F25);
        }
        bits = (long)version << 12 | rem;

        for (i = 0; i < 6; i++) {
            for (j = 0; j < 3; j++) {
                k = qrsize - 11 + j;
                setModuleBounded(qrcode, k, i, (int)(bits & 1));
                setModuleBounded(qrcode, i, k, (int)(bits & 1));
                bits >>= 1;
            }
        }
    }
}


// Draws two copies of the format bits (with its own error correction code) based
// on the given mask and error correction level. This always draws all modules of
// the format bits, unlike drawLightFunctionModules() which might skip dark modules.
static void drawFormatBits(enum qrcodegen_Ecc ecl, enum qrcodegen_Mask mask, uint8_t qrcode[]) {
    static const int table[] = {1, 0, 3, 2};
    int data;
    int rem;
    int bits;
    int i;
    int qrsize;

    assert(0 <= (int)mask && (int)mask <= 7);

    data = table[(int)ecl] << 3 | (int)mask;
    rem = data;
    for (i = 0; i < 10; i++) {
        rem = (rem << 1) ^ ((rem >> 9) * 0x537);
    }
    bits = (data << 10 | rem) ^ 0x5412;
    
    assert(bits >> 15 == 0);
    
    for (i = 0; i <= 5; i++) {
        setModuleBounded(qrcode, 8, i, getBit(bits, i));
    }
    setModuleBounded(qrcode, 8, 7, getBit(bits, 6));
    setModuleBounded(qrcode, 8, 8, getBit(bits, 7));
    setModuleBounded(qrcode, 7, 8, getBit(bits, 8));
    for (i = 9; i < 15; i++) {
        setModuleBounded(qrcode, 14 - i, 8, getBit(bits, i));
    }
    
    qrsize = qrcodegen_getSize(qrcode);
    for (i = 0; i < 8; i++) {
        setModuleBounded(qrcode, qrsize - 1 - i, 8, getBit(bits, i));
    }
    for (i = 8; i < 15; i++) {
        setModuleBounded(qrcode, 8, qrsize - 15 + i, getBit(bits, i));
    }
    setModuleBounded(qrcode, 8, qrsize - 8, 1);
}


// Calculates and stores an ascending list of positions of alignment patterns
// for this version number, returning the length of the list (in the range [0,7]).
// Each position is in the range [0,177), and are used on both the x and y axes.
// This could be implemented as lookup table of 40 variable-length lists of unsigned bytes.
testable int getAlignmentPatternPositions(int version, uint8_t result[7])
{
    int numAlign;
    int step;
    int i;
    int pos;

    if (version == 1)
        return 0;

    numAlign = version / 7 + 2;
    step = (version * 8 + numAlign * 3 + 5) / (numAlign * 4 - 4) * 2;

    pos = version * 4 + 10;
    for (i = numAlign - 1; i >= 1; i--) {
        result[i] = (uint8_t)pos;
        pos -= step;
    }

    result[0] = 6;
    return numAlign;
}



// Sets every module in the range [left : left + width] * [top : top + height] to dark.
static void fillRectangle(int left, int top, int width, int height, uint8_t qrcode[])
{
    int dy;
    int dx;

    for (dy = 0; dy < height; dy++) {
        for (dx = 0; dx < width; dx++)
            setModuleBounded(qrcode, left + dx, top + dy, true);
    }
}




/*---- Drawing data modules and masking ----*/

// Draws the raw codewords (including data and ECC) onto the given QR Code. This requires the initial state of
// the QR Code to be dark at function modules and light at codeword modules (including unused remainder bits).
static void drawCodewords(const uint8_t data[], int dataLen, uint8_t qrcode[])
{
    int qrsize;
    int i;
    int right;
    int vert;
    int j;
    int x;
    int y;
    int upward;
    int dark;

    qrsize = qrcodegen_getSize(qrcode);
    i = 0;

    for (right = qrsize - 1; right >= 1; right -= 2) {
        if (right == 6)
            right = 5;

        for (vert = 0; vert < qrsize; vert++) {
            for (j = 0; j < 2; j++) {
                x = right - j;
                upward = ((right + 1) & 2) == 0;
                y = upward ? qrsize - 1 - vert : vert;

                if (!getModuleBounded(qrcode, x, y) && i < dataLen * 8) {
                    dark = getBit(data[i >> 3], 7 - (i & 7));
                    setModuleBounded(qrcode, x, y, dark);
                    i++;
                }
            }
        }
    }

    assert(i == dataLen * 8);
}



// XORs the codeword modules in this QR Code with the given mask pattern
// and given pattern of function modules. The codeword bits must be drawn
// before masking. Due to the arithmetic of XOR, calling applyMask() with
// the same mask value a second time will undo the mask. A final well-formed
// QR Code needs exactly one (not zero, two, etc.) mask applied.
static void applyMask(const uint8_t functionModules[], uint8_t qrcode[], enum qrcodegen_Mask mask) {
    int qrsize;
    int x;
    int y;
    int invert;
    int val;

    assert(0 <= (int)mask && (int)mask <= 7);
    qrsize = qrcodegen_getSize(qrcode);

    for (y = 0; y < qrsize; y++) {
        for (x = 0; x < qrsize; x++) {
            if (getModuleBounded(functionModules, x, y)) {
                continue;
            }

            invert = 0;
            switch ((int)mask) {
                case 0:  invert = (x + y) % 2 == 0;                    break;
                case 1:  invert = y % 2 == 0;                          break;
                case 2:  invert = x % 3 == 0;                          break;
                case 3:  invert = (x + y) % 3 == 0;                    break;
                case 4:  invert = (x / 3 + y / 2) % 2 == 0;            break;
                case 5:  invert = (x * y % 2 + x * y % 3) == 0;        break;
                case 6:  invert = (x * y % 2 + x * y % 3) % 2 == 0;    break;
                case 7:  invert = ((x + y) % 2 + x * y % 3) % 2 == 0;  break;
                default: break;
            }
            
            val = getModuleBounded(qrcode, x, y);
            setModuleBounded(qrcode, x, y, val ^ invert);
        }
    }
}


// Calculates and returns the penalty score based on state of the given QR Code's current modules.
// This is used by the automatic mask choice algorithm to find the mask pattern that yields the lowest score.
static long getPenaltyScore(const uint8_t qrcode[]) {
    int qrsize;
    long result;
    int x, y;
    int dark;
    int total;
    int k;

    qrsize = qrcodegen_getSize(qrcode);
    result = 0;
    
    for (y = 0; y < qrsize; y++) {
        int runColor = 0;
        int runX = 0;
        int runHistory[7];
        runHistory[0] = 0;
        runHistory[1] = 0;
        runHistory[2] = 0;
        runHistory[3] = 0;
        runHistory[4] = 0;
        runHistory[5] = 0;
        runHistory[6] = 0;

        for (x = 0; x < qrsize; x++) {
            if (getModuleBounded(qrcode, x, y) == runColor) {
                runX++;
                if (runX == 5)
                    result += PENALTY_N1;
                else if (runX > 5)
                    result++;
            } else {
                finderPenaltyAddHistory(runX, runHistory, qrsize);
                if (!runColor)
                    result += finderPenaltyCountPatterns(runHistory, qrsize) * PENALTY_N3;
                runColor = getModuleBounded(qrcode, x, y);
                runX = 1;
            }
        }
        result += finderPenaltyTerminateAndCount(runColor, runX, runHistory, qrsize) * PENALTY_N3;
    }

    for (x = 0; x < qrsize; x++) {
        int runColor = 0;
        int runY = 0;
        int runHistory[7];
        runHistory[0] = 0;
        runHistory[1] = 0;
        runHistory[2] = 0;
        runHistory[3] = 0;
        runHistory[4] = 0;
        runHistory[5] = 0;
        runHistory[6] = 0;

        for (y = 0; y < qrsize; y++) {
            if (getModuleBounded(qrcode, x, y) == runColor) {
                runY++;
                if (runY == 5)
                    result += PENALTY_N1;
                else if (runY > 5)
                    result++;
            } else {
                finderPenaltyAddHistory(runY, runHistory, qrsize);
                if (!runColor)
                    result += finderPenaltyCountPatterns(runHistory, qrsize) * PENALTY_N3;
                runColor = getModuleBounded(qrcode, x, y);
                runY = 1;
            }
        }
        result += finderPenaltyTerminateAndCount(runColor, runY, runHistory, qrsize) * PENALTY_N3;
    }
    
    for (y = 0; y < qrsize - 1; y++) {
        for (x = 0; x < qrsize - 1; x++) {
            int color = getModuleBounded(qrcode, x, y);
            if (  color == getModuleBounded(qrcode, x + 1, y) &&
                  color == getModuleBounded(qrcode, x, y + 1) &&
                  color == getModuleBounded(qrcode, x + 1, y + 1))
                result += PENALTY_N2;
        }
    }
    
    dark = 0;
    for (y = 0; y < qrsize; y++) {
        for (x = 0; x < qrsize; x++) {
            if (getModuleBounded(qrcode, x, y))
                dark++;
        }
    }

    total = qrsize * qrsize;
    k = (int)((labs(dark * 20L - total * 10L) + total - 1) / total) - 1;
    assert(0 <= k && k <= 9);
    result += k * PENALTY_N4;
    assert(0 <= result && result <= 2568888L);
    return result;
}


// Can only be called immediately after a light run is added, and
// returns either 0, 1, or 2. A helper function for getPenaltyScore().
static int finderPenaltyCountPatterns(const int runHistory[7], int qrsize) {
    int n;
    int core;
    n = runHistory[1];
    assert(n <= qrsize * 3);
    (void)qrsize;

    core = (n > 0 && 
            runHistory[2] == n && 
            runHistory[3] == n * 3 && 
            runHistory[4] == n && 
            runHistory[5] == n);

    return (core && runHistory[0] >= n * 4 && runHistory[6] >= n ? 1 : 0)
         + (core && runHistory[6] >= n * 4 && runHistory[0] >= n ? 1 : 0);
}


// Must be called at the end of a line (row or column) of modules. A helper function for getPenaltyScore().
static int finderPenaltyTerminateAndCount(bool currentRunColor, int currentRunLength, int runHistory[7], int qrsize) {
	if (currentRunColor) {  // Terminate dark run
		finderPenaltyAddHistory(currentRunLength, runHistory, qrsize);
		currentRunLength = 0;
	}
	currentRunLength += qrsize;  // Add light border to final run
	finderPenaltyAddHistory(currentRunLength, runHistory, qrsize);
	return finderPenaltyCountPatterns(runHistory, qrsize);
}


// Pushes the given value to the front and drops the last value. A helper function for getPenaltyScore().
static void finderPenaltyAddHistory(int currentRunLength, int runHistory[7], int qrsize) {
	if (runHistory[0] == 0)
		currentRunLength += qrsize;  // Add light border to initial run
	memmove(&runHistory[1], &runHistory[0], 6 * sizeof(runHistory[0]));
	runHistory[0] = currentRunLength;
}



/*---- Basic QR Code information ----*/

int qrcodegen_getSize(const uint8_t qrcode[]) {
    int result;
    assert(qrcode != NULL);
    result = qrcode[0];
    assert((qrcodegen_VERSION_MIN * 4 + 17) <= result
        && result <= (qrcodegen_VERSION_MAX * 4 + 17));
    return result;
}

bool qrcodegen_getModule(const uint8_t qrcode[], int x, int y) {
    int qrsize;
    assert(qrcode != NULL);
    qrsize = qrcode[0];
    return (0 <= x && x < qrsize && 0 <= y && y < qrsize) && getModuleBounded(qrcode, x, y);
}

testable bool getModuleBounded(const uint8_t qrcode[], int x, int y) {
    int qrsize;
    int index;
    qrsize = qrcode[0];
    assert(21 <= qrsize && qrsize <= 177 && 0 <= x && x < qrsize && 0 <= y && y < qrsize);
    index = y * qrsize + x;
    return getBit(qrcode[(index >> 3) + 1], index & 7);
}


testable void setModuleBounded(uint8_t qrcode[], int x, int y, bool isDark) {
    int qrsize;
    int index;
    int bitIndex;
    int byteIndex;

    qrsize = qrcode[0];
    assert(21 <= qrsize && qrsize <= 177 && 0 <= x && x < qrsize && 0 <= y && y < qrsize);

    index = y * qrsize + x;
    bitIndex = index & 7;
    byteIndex = (index >> 3) + 1;

    if (isDark)
        qrcode[byteIndex] |= 1 << bitIndex;
    else
        qrcode[byteIndex] &= (1 << bitIndex) ^ 0xFF;
}


// Sets the color of the module at the given coordinates, doing nothing if out of bounds.
#include "qrcodegen.h"

testable void setModuleUnbounded(uint8_t qrcode[], int x, int y, bool isDark) {
	int qrsize = qrcode[0];
	if (0 <= x && x < qrsize && 0 <= y && y < qrsize)
		setModuleBounded(qrcode, x, y, isDark);
}


// Returns true iff the i'th bit of x is set to 1. Requires x >= 0 and 0 <= i <= 14.
static bool getBit(int x, int i) {
	return ((x >> i) & 1) != 0;
}



/*---- Segment handling ----*/

// Public function - see documentation comment in header file.
bool qrcodegen_isNumeric(const char *text) {
	assert(text != NULL);
	for (; *text != '\0'; text++) {
		if (*text < '0' || *text > '9')
			return false;
	}
	return true;
}


// Public function - see documentation comment in header file.
bool qrcodegen_isAlphanumeric(const char *text) {
	assert(text != NULL);
	for (; *text != '\0'; text++) {
		if (strchr(ALPHANUMERIC_CHARSET, *text) == NULL)
			return false;
	}
	return true;
}


// Public function - see documentation comment in header file.
size_t qrcodegen_calcSegmentBufferSize(enum qrcodegen_Mode mode, size_t numChars)
{
    int temp;

    temp = calcSegmentBitLength(mode, numChars);
    if (temp == LENGTH_OVERFLOW)
        return SIZE_MAX;

  //  assert(temp <= INT16_MAX);

    return ((size_t)temp + 7) / 8;
}


// Returns the number of data bits needed to represent a segment
// containing the given number of characters using the given mode. Notes:
// - Returns LENGTH_OVERFLOW on failure, i.e. numChars > INT16_MAX
//   or the number of needed bits exceeds INT16_MAX (i.e. 32767).
// - Otherwise, all valid results are in the range [0, INT16_MAX].
// - For byte mode, numChars measures the number of bytes, not Unicode code points.
// - For ECI mode, numChars must be 0, and the worst-case number of bits is returned.
//   An actual ECI segment can have shorter data. For non-ECI modes, the result is exact.
testable int calcSegmentBitLength(enum qrcodegen_Mode mode, size_t numChars) {
    long result;
    if (numChars > (unsigned int)INT16_MAX)
        return LENGTH_OVERFLOW;
    
    result = (long)numChars;
    if (mode == qrcodegen_Mode_NUMERIC)
        result = (result * 10 + 2) / 3;
    else if (mode == qrcodegen_Mode_ALPHANUMERIC)
        result = (result * 11 + 1) / 2;
    else if (mode == qrcodegen_Mode_BYTE)
        result *= 8;
    else if (mode == qrcodegen_Mode_KANJI)
        result *= 13;
    else if (mode == qrcodegen_Mode_ECI && numChars == 0)
        result = 3 * 8;
    else {
        assert(0);
        return LENGTH_OVERFLOW;
    }
    
    assert(result >= 0);
    if (result > INT16_MAX)
        return LENGTH_OVERFLOW;
    return (int)result;
}


void qrcodegen_makeBytes(const uint8_t data[], size_t len, uint8_t buf[], struct qrcodegen_Segment *result) {
    assert(data != NULL || len == 0);
    
    result->mode = qrcodegen_Mode_BYTE;
    result->bitLength = calcSegmentBitLength(result->mode, len);
    
    assert(result->bitLength != (long) -1);
    
    result->numChars = (int)len;
    if (len > 0) {
        memcpy(buf, data, len);
    }
    result->data = buf;
}


// Public function - see documentation comment in header file.
void qrcodegen_makeNumeric(const char *digits, uint8_t buf[], struct qrcodegen_Segment *result) {
    size_t len;
    int bitLen;
    unsigned int accumData;
    int accumCount;
    char c;

    if (!digits || !result)
        return;

    len = strlen(digits);
    result->mode = qrcodegen_Mode_NUMERIC;
    bitLen = calcSegmentBitLength(result->mode, len);
    if (bitLen == -1)
        return;

    result->numChars = (int)len;
    if (bitLen > 0)
        memset(buf, 0, ((size_t)bitLen + 7) / 8);

    result->bitLength = 0;
    accumData = 0;
    accumCount = 0;

    for (; *digits != '\0'; digits++) {
        c = *digits;
        if (c < '0' || c > '9')
            return;
        accumData = accumData * 10 + (unsigned int)(c - '0');
        accumCount++;
        if (accumCount == 3) {
            appendBitsToBuffer(accumData, 10, buf, &result->bitLength);
            accumData = 0;
            accumCount = 0;
        }
    }

    if (accumCount > 0)
        appendBitsToBuffer(accumData, accumCount * 3 + 1, buf, &result->bitLength);

    if (result->bitLength != bitLen)
        return;

    result->data = buf;
}




// Public function - see documentation comment in header file.
void qrcodegen_makeAlphanumeric(const char *text, uint8_t buf[], struct qrcodegen_Segment *result) {
    size_t len;
    int bitLen;
    unsigned int accumData;
    int accumCount;
    const char *temp;
    char c;

    assert(text != NULL);
    assert(result != NULL);

    len = strlen(text);
    result->mode = qrcodegen_Mode_ALPHANUMERIC;
    bitLen = calcSegmentBitLength(result->mode, len);
    assert(bitLen != (int)-1);

    result->numChars = (int)len;
    if (bitLen > 0) {
        memset(buf, 0, ((size_t)bitLen + 7) / 8);
    }
    result->bitLength = 0;

    accumData = 0;
    accumCount = 0;
    for (; *text != '\0'; text++) {
        c = *text;
        temp = strchr(ALPHANUMERIC_CHARSET, c);
        assert(temp != NULL);
        
        accumData = accumData * 45 + (unsigned int)(temp - ALPHANUMERIC_CHARSET);
        accumCount++;
        
        if (accumCount == 2) {
            appendBitsToBuffer(accumData, 11, buf, &result->bitLength);
            accumData = 0;
            accumCount = 0;
        }
    }

    if (accumCount > 0) {
        appendBitsToBuffer(accumData, 6, buf, &result->bitLength);
    }

    assert(result->bitLength == bitLen);
    result->data = buf;
}


// Public function - see documentation comment in header file.
void qrcodegen_makeEci(long assignVal, uint8_t buf[], struct qrcodegen_Segment *result) {
    assert(result != NULL);

    result->mode = qrcodegen_Mode_ECI;
    result->numChars = 0;
    result->bitLength = 0;

    if (assignVal < 0) {
        assert(0);
    } else if (assignVal < (1L << 7)) {
        memset(buf, 0, 1);
        appendBitsToBuffer((unsigned int)assignVal, 8, buf, &result->bitLength);
    } else if (assignVal < (1L << 14)) {
        memset(buf, 0, 2);
        appendBitsToBuffer(2, 2, buf, &result->bitLength);
        appendBitsToBuffer((unsigned int)assignVal, 14, buf, &result->bitLength);
    } else if (assignVal < 1000000L) {
        memset(buf, 0, 3);
        appendBitsToBuffer(6, 3, buf, &result->bitLength);
        appendBitsToBuffer((unsigned int)(assignVal >> 10), 11, buf, &result->bitLength);
        appendBitsToBuffer((unsigned int)(assignVal & 0x3FF), 10, buf, &result->bitLength);
    } else {
        assert(0);
    }

    result->data = buf;
}


// Calculates the number of bits needed to encode the given segments at the given version.
// Returns a non-negative number if successful. Otherwise returns LENGTH_OVERFLOW if a segment
// has too many characters to fit its length field, or the total bits exceeds INT16_MAX.
int getTotalBits(const struct qrcodegen_Segment segs[], size_t len, int version) {
    long result = 0;
    size_t i;

    if (!segs && len != 0)
        return LENGTH_OVERFLOW;

    for (i = 0; i < len; i++) {
        int numChars  = segs[i].numChars;
        int bitLength = segs[i].bitLength;
        int ccbits;

        ccbits = numCharCountBits(segs[i].mode, version);
        if (ccbits < 0 || ccbits > 16)
            return LENGTH_OVERFLOW;

        if (numChars >= (1L << ccbits))
            return LENGTH_OVERFLOW;

        result += 4L + ccbits + bitLength;
        if (result > INT16_MAX)
            return LENGTH_OVERFLOW;
    }

    return (int)result;
}



// Returns the bit width of the character count field for a segment in the given mode
// in a QR Code at the given version number. The result is in the range [0, 16].
static int numCharCountBits(enum qrcodegen_Mode mode, int version) {
    int i;

    if (version < qrcodegen_VERSION_MIN || version > qrcodegen_VERSION_MAX)
        return -1;

    i = (version + 7) / 17;
    switch (mode) {
        case qrcodegen_Mode_NUMERIC: {
            static const int temp[] = {10, 12, 14};
            return temp[i];
        }
        case qrcodegen_Mode_ALPHANUMERIC: {
            static const int temp[] = {9, 11, 13};
            return temp[i];
        }
        case qrcodegen_Mode_BYTE: {
            static const int temp[] = {8, 16, 16};
            return temp[i];
        }
        case qrcodegen_Mode_KANJI: {
            static const int temp[] = {8, 10, 12};
            return temp[i];
        }
        case qrcodegen_Mode_ECI:
            return 0;
        default:
            return -1;
    }
}



#undef LENGTH_OVERFLOW

