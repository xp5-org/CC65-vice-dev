


////////////////////////////////////////////////////////////////
// QR code demo for 8-bit computers.
// https://8bitworkshop.com/docs/posts/2022/8bit-qr-code.html
// Uses qrtiny:
// - https://github.com/danielgjackson/qrtiny
// - Copyright (c) 2020, Dan Jackson. All rights reserved.
////////////////////////////////////////////////////////////////


#include <stdio.h>
#include <tgi.h>


#include <stdio.h>
#include <conio.h>
#include <string.h>
#include <cbm_petscii_charmap.h>
//#include "common.h"  // assuming this contains VIC definitions and joy_* functions



#define QRTINY_MODULE_LIGHT 0
#define QRTINY_MODULE_DARK 1
#define QRTINY_MODULE_DATA -1
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>



#define SPRITE_WIDTH 21
#define SPRITE_HEIGHT 21
#define BYTES_PER_ROW ((SPRITE_WIDTH + 7) / 8)  /* 3 bytes for 21 pixels */




// Quiet space around marker
#define QRTINY_QUIET_NONE 0
#define QRTINY_QUIET_STANDARD 4

// This tiny creator only supports V1 QR Codes, 21x21 modules
#define QRTINY_VERSION 1
#define QRTINY_DIMENSION 21

#define QRTINY_TOTAL_CAPACITY \
    (((16 * (size_t)1 + 128) * (size_t)1) + 64 \
    - 0 \
    - 0)

// Required buffer size
#define QRTINY_BUFFER_SIZE (((QRTINY_TOTAL_CAPACITY) + 7) >> 3)

// 0b00 Error-Correction Medium   (~15%, 10 codewords), V1 fits: 14 full characters / 20 alphanumeric / 34 numeric
#define QRTINY_FORMATINFO_MASK_000_ECC_MEDIUM   0x5412
#define QRTINY_FORMATINFO_MASK_001_ECC_MEDIUM   0x5125
#define QRTINY_FORMATINFO_MASK_010_ECC_MEDIUM   0x5e7c
#define QRTINY_FORMATINFO_MASK_011_ECC_MEDIUM   0x5b4b
#define QRTINY_FORMATINFO_MASK_100_ECC_MEDIUM   0x45f9
#define QRTINY_FORMATINFO_MASK_101_ECC_MEDIUM   0x40ce
#define QRTINY_FORMATINFO_MASK_110_ECC_MEDIUM   0x4f97
#define QRTINY_FORMATINFO_MASK_111_ECC_MEDIUM   0x4aa0
// 0b01 Error-Correction Low      (~ 7%,  7 codewords), V1 fits: 17 full characters / 26 alphanumeric / 41 numeric
#define QRTINY_FORMATINFO_MASK_000_ECC_LOW      0x77c4
#define QRTINY_FORMATINFO_MASK_001_ECC_LOW      0x72f3
#define QRTINY_FORMATINFO_MASK_010_ECC_LOW      0x7daa
#define QRTINY_FORMATINFO_MASK_011_ECC_LOW      0x789d
#define QRTINY_FORMATINFO_MASK_100_ECC_LOW      0x662f
#define QRTINY_FORMATINFO_MASK_101_ECC_LOW      0x6318
#define QRTINY_FORMATINFO_MASK_110_ECC_LOW      0x6c41
#define QRTINY_FORMATINFO_MASK_111_ECC_LOW      0x6976
// 0b10 Error-Correction High     (~30%, 17 codewords), V1 fits:  7 full characters / 10 alphanumeric / 17 numeric
#define QRTINY_FORMATINFO_MASK_000_ECC_HIGH     0x1689
#define QRTINY_FORMATINFO_MASK_001_ECC_HIGH     0x13be
#define QRTINY_FORMATINFO_MASK_010_ECC_HIGH     0x1ce7
#define QRTINY_FORMATINFO_MASK_011_ECC_HIGH     0x19d0
#define QRTINY_FORMATINFO_MASK_100_ECC_HIGH     0x0762
#define QRTINY_FORMATINFO_MASK_101_ECC_HIGH     0x0255
#define QRTINY_FORMATINFO_MASK_110_ECC_HIGH     0x0d0c
#define QRTINY_FORMATINFO_MASK_111_ECC_HIGH     0x083b
// 0b11 Error-Correction Quartile (~25%, 13 codewords), V1 fits: 11 full characters / 16 alphanumeric / 27 numeric
#define QRTINY_FORMATINFO_MASK_000_ECC_QUARTILE 0x355f
#define QRTINY_FORMATINFO_MASK_001_ECC_QUARTILE 0x3068
#define QRTINY_FORMATINFO_MASK_010_ECC_QUARTILE 0x3f31
#define QRTINY_FORMATINFO_MASK_011_ECC_QUARTILE 0x3a06
#define QRTINY_FORMATINFO_MASK_100_ECC_QUARTILE 0x24b4
#define QRTINY_FORMATINFO_MASK_101_ECC_QUARTILE 0x2183
#define QRTINY_FORMATINFO_MASK_110_ECC_QUARTILE 0x2eda
#define QRTINY_FORMATINFO_MASK_111_ECC_QUARTILE 0x2bed

#define QRTINY_FORMATINFO_MASK 0x5412               // 0b0101010000010010
#define QRTINY_FORMATINFO_TO_ECL(_v) ((((_v) ^ QRTINY_FORMATINFO_MASK) >> (QRTINY_SIZE_BCH + QRTINY_SIZE_MASK)) & ((1 << QRTINY_SIZE_ECL) - 1))
#define QRTINY_FORMATINFO_TO_MASKPATTERN(_v) ((((_v) ^ QRTINY_FORMATINFO_MASK) >> (QRTINY_SIZE_BCH)) & ((1 << QRTINY_SIZE_MASK) - 1))

#define QRTINY_SIZE_ECL 2                           // 2-bit code for error correction
#define QRTINY_SIZE_MASK 3                          // 3-bit code for mask size
#define QRTINY_SIZE_BCH 10                          // 10,5 BCH for format information
#define QRTINY_SIZE_MODE_INDICATOR 4                // 4-bit mode indicator

#define QRTINY_MODE_INDICATOR_NUMERIC      0x1      // 0b0001 Numeric (maximal groups of 3/2/1 digits encoded to 10/7/4-bit binary)
#define QRTINY_MODE_INDICATOR_ALPHANUMERIC 0x2      // 0b0010 Alphanumeric ('0'-'9', 'A'-'Z', ' ', '$', '%', '*', '+', '-', '.', '/', ':') -> 0-44 index. Pairs combined (a*45+b) encoded as 11-bit; odd remainder encoded as 6-bit.
#define QRTINY_MODE_INDICATOR_8_BIT        0x4      // 0b0100 8-bit byte
#define QRTINY_MODE_INDICATOR_TERMINATOR   0x0      // 0b0000 Terminator (End of Message)

#define QRTINY_MODE_NUMERIC_COUNT_BITS      10      // for V1
#define QRTINY_MODE_ALPHANUMERIC_COUNT_BITS  9      // for V1
#define QRTINY_MODE_8BIT_COUNT_BITS          8      // for V1
// Segment buffer sizes (payload, 4-bit mode indicator, V1 sized char count)
#define QRTINY_SEGMENT_NUMERIC_BUFFER_BITS(_c) (QRTINY_SIZE_MODE_INDICATOR + QRTINY_MODE_NUMERIC_COUNT_BITS + (10 * ((_c) / 3)) + (((_c) % 3) * 4) - (((_c) % 3) / 2))
#define QRTINY_SEGMENT_ALPHANUMERIC_BUFFER_BITS(_c) (QRTINY_SIZE_MODE_INDICATOR + QRTINY_MODE_ALPHANUMERIC_COUNT_BITS + 11 * ((_c) >> 1) + 6 * ((_c) & 1))
#define QRTINY_SEGMENT_8_BIT_BUFFER_BITS(_c) (QRTINY_SIZE_MODE_INDICATOR + QRTINY_MODE_8BIT_COUNT_BITS + 8 * (_c))

#define QRTINY_FINDER_SIZE 7
#define QRTINY_TIMING_OFFSET 6
#define QRTINY_VERSION_SIZE 3
#define QRTINY_ALIGNMENT_RADIUS 2


static const uint8_t eccDivisorsMedium[] = { 0xd8, 0xc2, 0x9f, 0x6f, 0xc7, 0x5e, 0x5f, 0x71, 0x9d, 0xc1 }; // V1 0b00 Medium ECL
static const uint8_t eccDivisorsLow[] = { 0x7f, 0x7a, 0x9a, 0xa4, 0x0b, 0x44, 0x75 }; // V1 0b01 Low ECL
static const uint8_t eccDivisorsHigh[] = { 0x77, 0x42, 0x53, 0x78, 0x77, 0x16, 0xc5, 0x53, 0xf9, 0x29, 0x8f, 0x86, 0x55, 0x35, 0x7d, 0x63, 0x4f }; // V1 0b10 High ECL
static const uint8_t eccDivisorsQuartile[] = { 0x89, 0x49, 0xe3, 0x11, 0xb1, 0x11, 0x34, 0x0d, 0x2e, 0x2b, 0x53, 0x84, 0x78 }; // V1 0b11 Quartile ECL
static const uint8_t *eccDivisors[1 << QRTINY_SIZE_ECL] = { eccDivisorsMedium, eccDivisorsLow, eccDivisorsHigh, eccDivisorsQuartile };

  
// Encode one or more segments of text to the buffer (at bit offset specified), returning the number of bits written. Caller must ensure buffer has capacity.
size_t QrTinyWriteNumeric(void *buffer, size_t offset, const char *text);       // 17-41 digits, depending on ECC.
size_t QrTinyWriteAlphanumeric(void *buffer, size_t offset, const char *text);  // 10-26 characters (upper-case/digits/symbols), depending on ECC.
size_t QrTinyWrite8Bit(void *buffer, size_t offset, const char *text);          //  7-17 8-bit characters, depending on ECC.

// Compute the remaining buffer contents: any required padding and the calculated error-correction information
bool QrTinyGenerate(uint8_t *buffer, size_t payloadLength, uint16_t formatInfo);

// Get the module at the given coordinate (0=light, 1=dark)
int QrTinyModuleGet(uint8_t *buffer, uint16_t formatInfo, int x, int y);







static const unsigned char g_exp[256] = {
    0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80,0x1D,0x3A,0x74,0xE8,0xCD,0x87,0x13,0x26,
    0x4C,0x98,0x2D,0x5A,0xB4,0x75,0xEA,0xC9,0x8F,0x03,0x06,0x0C,0x18,0x30,0x60,0xC0,
    0x9D,0x27,0x4E,0x9C,0x25,0x4A,0x94,0x35,0x6A,0xD4,0xB5,0x77,0xEE,0xC1,0x9F,0x23,
    0x46,0x8C,0x05,0x0A,0x14,0x28,0x50,0xA0,0x5D,0xBA,0x69,0xD2,0xB9,0x6F,0xDE,0xA1,
    0x5F,0xBE,0x61,0xC2,0x99,0x2F,0x5E,0xBC,0x65,0xCA,0x89,0x0F,0x1E,0x3C,0x78,0xF0,
    0xFD,0xE7,0xD3,0xBB,0x6B,0xD6,0xB1,0x7F,0xFE,0xE1,0xDF,0xA3,0x5B,0xB6,0x71,0xE2,
    0xD9,0xAF,0x43,0x86,0x11,0x22,0x44,0x88,0x0D,0x1A,0x34,0x68,0xD0,0xBD,0x67,0xCE,
    0x81,0x1F,0x3E,0x7C,0xF8,0xED,0xC7,0x93,0x3B,0x76,0xEC,0xC5,0x97,0x33,0x66,0xCC,
    0x85,0x17,0x2E,0x5C,0xB8,0x6D,0xDA,0xA9,0x4F,0x9E,0x21,0x42,0x84,0x15,0x2A,0x54,
    0xA8,0x4D,0x9A,0x29,0x52,0xA4,0x55,0xAA,0x49,0x92,0x39,0x72,0xE4,0xD5,0xB7,0x73,
    0xE6,0xD1,0xBF,0x63,0xC6,0x91,0x3F,0x7E,0xFC,0xE5,0xD7,0xB3,0x7B,0xF6,0xF1,0xFF,
    0xE3,0xDB,0xAB,0x4B,0x96,0x31,0x62,0xC4,0x95,0x37,0x6E,0xDC,0xA5,0x57,0xAE,0x41,
    0x82,0x19,0x32,0x64,0xC8,0x8D,0x07,0x0E,0x1C,0x38,0x70,0xE0,0xDD,0xA7,0x53,0xA6,
    0x51,0xA2,0x59,0xB2,0x79,0xF2,0xF9,0xEF,0xC3,0x9B,0x2B,0x56,0xAC,0x45,0x8A,0x09,
    0x12,0x24,0x48,0x90,0x3D,0x7A,0xF4,0xF5,0xF7,0xF3,0xFB,0xEB,0xCB,0x8B,0x0B,0x16,
    0x2C,0x58,0xB0,0x7D,0xFA,0xE9,0xCF,0x83,0x1B,0x36,0x6C,0xD8,0xAD,0x47,0x8E,0x01
};

static const unsigned char g_log[256] = {
    0x00,0x00,0x01,0x19,0x02,0x32,0x1A,0xC6,0x03,0xDF,0x33,0xEE,0x1B,0x68,0xC7,0x4B,
    0x04,0x64,0xE0,0x0E,0x34,0x8D,0xEF,0x81,0x1C,0xC1,0x69,0xF8,0xC8,0x12,0x4C,0x71,
    0x05,0x8A,0x65,0x2F,0xE1,0x24,0x0F,0xA6,0x35,0x9A,0x8E,0x92,0xF0,0x17,0x82,0x45,
    0x1D,0xB5,0xC2,0x7D,0x6A,0x27,0xF9,0xB9,0xC9,0x94,0x13,0x62,0x4D,0x54,0x72,0x3D,
    0x06,0xBC,0x8B,0x62,0x66,0x48,0x30,0x5E,0xE2,0x58,0x25,0x0A,0x10,0x85,0xA7,0x88,
    0x36,0xD0,0x9B,0xCE,0x8F,0x76,0x93,0x7B,0xF1,0xD7,0x18,0x5A,0x83,0x3B,0x46,0x40,
    0x1E,0x3A,0xB6,0x93,0xC3,0x48,0x7E,0x6E,0x6B,0x3A,0x28,0xAB,0xFA,0x87,0xBA,0x3D,
    0xCA,0x5E,0x95,0x9F,0x14,0x21,0x63,0x2B,0x4E,0x0F,0x55,0x11,0x73,0x7A,0x3E,0x53,
    0x07,0x70,0xBD,0x75,0x8C,0x82,0x63,0x0D,0x67,0x4A,0x49,0x20,0x31,0x12,0x5F,0x18,
    0xE3,0x79,0x59,0x77,0x26,0x12,0x0B,0x7C,0x11,0xA2,0x86,0x20,0xA8,0x1D,0x89,0x17,
    0x37,0xB4,0xD1,0x53,0x9C,0xBC,0xCF,0x51,0x90,0x72,0x77,0xAA,0x94,0x1D,0x7C,0x88,
    0xF2,0x1D,0xD8,0x6A,0x19,0xAC,0x5B,0x5E,0x84,0x1D,0x3C,0x1D,0x47,0x6A,0x41,0x12,
    0x1F,0x2D,0x3B,0x1D,0xB7,0x97,0x94,0x1D,0xC4,0x17,0x49,0xEC,0x7F,0x0C,0x6F,0xF6,
    0x6C,0xA1,0x3B,0x52,0x29,0x9D,0xAC,0x1D,0xFB,0x98,0x88,0x52,0xBB,0x14,0x3E,0x5D,
    0xCB,0x5D,0x5F,0x05,0x96,0x1D,0xA0,0x51,0x15,0xED,0x22,0x1D,0x64,0x70,0x2C,0x1D,
    0x4F,0x1D,0x10,0x1D,0x56,0x1D,0x12,0x1D,0x74,0x1D,0x7B,0x1D,0x3F,0x1D,0x54,0x00
};

static size_t QrTinyBufferAppend(uint8_t *buf, size_t pos, unsigned int val, unsigned char count) {
    unsigned char i;
    unsigned char bit_idx;
    uint8_t *ptr;
    for (i = 0; i < count; ++i) {
        ptr = buf + (pos >> 3);
        bit_idx = 7 - (pos & 7);
        if (val & (1 << (count - 1 - i)))
            *ptr |= (1 << bit_idx);
        else
            *ptr &= ~(1 << bit_idx);
        pos++;
    }
    return (size_t)count;
}

static int QrTinyIdentifyModule(unsigned char x, unsigned char y, uint16_t formatInfo) {
    unsigned char xx, yy;
    signed char formatIndex = -1;

    if (x >= QRTINY_DIMENSION || y >= QRTINY_DIMENSION) return QRTINY_MODULE_LIGHT;

    if ((x < 7 && y < 7) || (x > 13 && y < 7) || (x < 7 && y > 13)) {
        unsigned char lx = (x > 13) ? x - 14 : x;
        unsigned char ly = (y > 13) ? y - 14 : y;
        unsigned char dx = (lx > 3) ? lx - 3 : 3 - lx;
        unsigned char dy = (ly > 3) ? ly - 3 : 3 - ly;
        unsigned char maxD = (dx > dy) ? dx : dy;
        return (maxD & 1) ? QRTINY_MODULE_DARK : QRTINY_MODULE_LIGHT;
    }

    if (x == QRTINY_TIMING_OFFSET || y == QRTINY_TIMING_OFFSET) return ((x ^ y) & 1) ? QRTINY_MODULE_LIGHT : QRTINY_MODULE_DARK;

    xx = x - ((x >= QRTINY_TIMING_OFFSET) ? 1 : 0);
    yy = y - ((y >= QRTINY_TIMING_OFFSET) ? 1 : 0);

    if (x == 8 && y == 13) return QRTINY_MODULE_DARK;
    if (xx <= 7 && yy <= 7) formatIndex = 7 - xx + yy;
    else if (x == 8 && y >= 13) formatIndex = y - 7;
    else if (y == 8 && x >= 13) formatIndex = 20 - x;

    if (formatIndex >= 0) return (formatInfo >> formatIndex) & 1 ? QRTINY_MODULE_DARK : QRTINY_MODULE_LIGHT;

    return QRTINY_MODULE_DATA;
}

static void QrTinyRSRemainder(const uint8_t data[], unsigned char dataLen, const uint8_t generator[], unsigned char degree, uint8_t result[]) {
    unsigned char i, j, factor, logFactor;
    for (i = 0; i < degree; i++) result[i] = 0;

    for (i = 0; i < dataLen; i++) {
        factor = data[i] ^ result[0];
        for (j = 0; j < degree - 1; j++) result[j] = result[j + 1];
        result[degree - 1] = 0;

        if (factor != 0) {
            logFactor = g_log[factor];
            for (j = 0; j < degree; j++) {
                result[j] ^= g_exp[(logFactor + g_log[generator[j]]) % 255];
            }
        }
    }
}








// Write bits to buffer
// static size_t QrTinyBufferAppend(uint8_t *buf, size_t pos, uint32_t val, size_t count){
//     unsigned char i;
//     unsigned char bit_idx;
//     uint8_t *ptr;
//     for (i = 0; i < (unsigned char)count; ++i)
//     {
//         ptr = buf + (pos >> 3);
//         bit_idx = 7 - (pos & 7);
//         if (val & ((uint32_t)1 << (count - 1 - i)))
//             *ptr |= (1 << bit_idx);
//         else
//             *ptr &= ~(1 << bit_idx);
//         pos++;
//     }
//     return count;
// }


size_t QrTinyWriteNumeric(void *buffer, size_t bitPosition, const char *text){
    unsigned char remain;
    unsigned int value;
    unsigned char charCount = (unsigned char)strlen(text);

    bitPosition += QrTinyBufferAppend(buffer, bitPosition, QRTINY_MODE_INDICATOR_NUMERIC, QRTINY_SIZE_MODE_INDICATOR);
    bitPosition += QrTinyBufferAppend(buffer, bitPosition, (uint32_t)charCount, QRTINY_MODE_NUMERIC_COUNT_BITS);

    while (charCount > 0)
    {
        remain = charCount > 3 ? 3 : charCount;
        value = *text - '0';
        text++;

        if (remain > 1) 
        { 
            value = value * 10 + (*text - '0'); 
            text++;
            if (remain > 2) 
            { 
                value = value * 10 + (*text - '0'); 
                text++;
                bitPosition += QrTinyBufferAppend(buffer, bitPosition, value, 10);
            }
            else
            {
                bitPosition += QrTinyBufferAppend(buffer, bitPosition, value, 7);
            }
        }
        else
        {
            bitPosition += QrTinyBufferAppend(buffer, bitPosition, value, 4);
        }
        
        charCount -= remain;
    }

    return bitPosition;
}

static int QrGetAlphanumericVal(char c){
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'A' && c <= 'Z') return c - 'A' + 10;
    if (c >= 'a' && c <= 'z') return c - 'a' + 10;
    switch (c) {
        case ' ': return 36;
        case '$': return 37;
        case '%': return 38;
        case '*': return 39;
        case '+': return 40;
        case '-': return 41;
        case '.': return 42;
        case '/': return 43;
        case ':': return 44;
    }
    return 0;
}

size_t QrTinyWriteAlphanumeric(void *buffer, size_t bitPosition, const char *text){
    unsigned char charCount = (unsigned char)strlen(text);
    unsigned char remain = charCount;
    unsigned int value;

    bitPosition += QrTinyBufferAppend(buffer, bitPosition, QRTINY_MODE_INDICATOR_ALPHANUMERIC, QRTINY_SIZE_MODE_INDICATOR);
    bitPosition += QrTinyBufferAppend(buffer, bitPosition, (unsigned int)charCount, QRTINY_MODE_ALPHANUMERIC_COUNT_BITS);

    while (remain > 0)
    {
        value = (unsigned int)QrGetAlphanumericVal(*text++);
        if (remain > 1)
        {
            value = (value * 45) + QrGetAlphanumericVal(*text++);
            bitPosition += QrTinyBufferAppend(buffer, bitPosition, value, 11);
            remain -= 2;
        }
        else
        {
            bitPosition += QrTinyBufferAppend(buffer, bitPosition, value, 6);
            remain -= 1;
        }
    }
    return bitPosition;
}

size_t QrTinyWrite8Bit(void *buffer, size_t bitPosition, const char *text){
    unsigned char charCount = (unsigned char)strlen(text);
    unsigned char i;

    bitPosition += QrTinyBufferAppend(buffer, bitPosition, QRTINY_MODE_INDICATOR_8_BIT, QRTINY_SIZE_MODE_INDICATOR);
    bitPosition += QrTinyBufferAppend(buffer, bitPosition, (unsigned int)charCount, QRTINY_MODE_8BIT_COUNT_BITS);

    for (i = 0; i < charCount; i++)
    {
        bitPosition += QrTinyBufferAppend(buffer, bitPosition, (unsigned int)text[i], 8);
    }
    return bitPosition;
}

// Determine the data bit index for a V1 QR Code at a given coordinate (only valid at data module coordinates).
static const unsigned char qrmod3[] = {0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2};

static size_t QrTinyIdentifyIndex(unsigned char x, unsigned char y)
{
    unsigned char xx = x - ((x >= QRTINY_TIMING_OFFSET) ? 1 : 0);
    unsigned char yy = y - ((y >= QRTINY_TIMING_OFFSET) ? 1 : 0);
    unsigned char dir = (xx >> 1) & 1;
    unsigned char half = xx & 1;
    unsigned char h = 9 - (xx >> 1);
    unsigned char v = 4 - (yy >> 2);
    unsigned char module;
    unsigned char bit;
    
    if (h < 4) module = dir ? (h * 3 + v) : (h * 3 + 2 - v);
    else if (h < 6) module = 12 + (dir ? ((h-4) * 5 + v) : ((h-4) * 5 + 4 - v));
    else module = 22 + h - 6;

    bit = (((dir ? 0x0 : 0x3) ^ (yy & 3)) << 1) + half;
    return ((size_t)module << 3) | bit;
}






// static int QrTinyIdentifyModule(unsigned char x, unsigned char y, uint16_t formatInfo)
// {
//     unsigned char f, dx, dy, xx, yy;
//     signed char formatIndex = -1;

//     if (x >= QRTINY_DIMENSION || y >= QRTINY_DIMENSION) return QRTINY_MODULE_LIGHT;

//     for (f = 0; f < 3; f++)
//     {
//         unsigned char targetX = (f & 1 ? QRTINY_DIMENSION - 4 : 3);
//         unsigned char targetY = (f & 2 ? QRTINY_DIMENSION - 4 : 3);
//         dx = (x > targetX) ? x - targetX : targetX - x;
//         dy = (y > targetY) ? y - targetY : targetY - y;

//         if (dx == 0 && dy == 0) return QRTINY_MODULE_DARK;
//         if (dx <= 4 && dy <= 4)
//         {
//             unsigned char maxD = (dx > dy) ? dx : dy;
//             return (maxD & 1) ? QRTINY_MODULE_DARK : QRTINY_MODULE_LIGHT;
//         }
//     }

//     if (x == QRTINY_TIMING_OFFSET || y == QRTINY_TIMING_OFFSET) return ((x ^ y) & 1) ? QRTINY_MODULE_LIGHT : QRTINY_MODULE_DARK;

//     xx = x - ((x >= QRTINY_TIMING_OFFSET) ? 1 : 0);
//     yy = y - ((y >= QRTINY_TIMING_OFFSET) ? 1 : 0);

//     if (x == 8 && y == 13) return QRTINY_MODULE_DARK;
//     if (xx <= 7 && yy <= 7) formatIndex = 7 - xx + yy;
//     if (x == 8 && y >= 13) formatIndex = y + 14 - 20;
//     if (y == 8 && x >= 13) formatIndex = 20 - x;

//     if (formatIndex >= 0) return (formatInfo >> formatIndex) & 1 ? QRTINY_MODULE_DARK : QRTINY_MODULE_LIGHT;

//     return QRTINY_MODULE_DATA;
// }

static bool QrTinyCalculateMask(uint16_t formatInfo, unsigned char j, unsigned char i)
{
    switch (QRTINY_FORMATINFO_TO_MASKPATTERN(formatInfo))
    {
        case 0: return ((i + j) & 1) == 0;
        case 1: return (i & 1) == 0;
        case 2: return qrmod3[j] == 0;
        case 3: return qrmod3[i + j] == 0;
        case 4: return (((i >> 1) + (j / 3)) & 1) == 0;
        case 5: return ((i * j) & 1) + qrmod3[i * j] == 0;
        case 6: return ((((i * j) & 1) + qrmod3[i * j]) & 1) == 0;
        case 7: return ((qrmod3[i * j] + ((i + j) & 1)) & 1) == 0;
        default: return 0;
    }
}


// static void QrTinyRSRemainder(const uint8_t data[], unsigned char dataLen, const uint8_t generator[], unsigned char degree, uint8_t result[])
// {
//     unsigned char i, j, k, factor;
//     for (i = 0; i < degree; i++) result[i] = 0;

//     for (i = 0; i < dataLen; i++)
//     {
//         factor = data[i] ^ result[0];
//         for (j = 0; j < degree - 1; j++) result[j] = result[j + 1];
//         result[degree - 1] = 0;

//         for (j = 0; j < degree; j++)
//         {
//             unsigned char v = 0;
//             unsigned char g = generator[j];
//             for (k = 0; k < 8; k++)
//             {
//                 if (v & 0x80) v = (v << 1) ^ 0x1D;
//                 else v <<= 1;
//                 if (factor & (0x80 >> k)) v ^= g;
//             }
//             result[j] ^= v;
//         }
//     }
// }

#define QRTINY_ECC_CODEWORDS_MAX 17
// [Table 13] Number of error correction codewords (count of data 8-bit codewords in each block; for each error-correction level in V1)
static const int8_t qrcode_ecc_block_codewords[1 << QRTINY_SIZE_ECL] = {
    10, // 0b00 Medium
    7,  // 0b01 Low
    17, // 0b10 High
    13, // 0b11 Quartile
};


// Generate the code
bool QrTinyGenerate(uint8_t* buffer, size_t payloadLength, uint16_t formatInfo)
{
  size_t bitPosition;
  size_t remaining;
  size_t bits;
    // Number of error correction blocks (count of error-correction-blocks; for each error-correction level in V1)
    int errorCorrectionLevel = QRTINY_FORMATINFO_TO_ECL(formatInfo);
    int eccCodewords = qrcode_ecc_block_codewords[errorCorrectionLevel]; // (sizeof(eccDivisors[errorCorrectionLevel]) / sizeof(eccDivisors[errorCorrectionLevel][0]));
    const uint8_t *eccDivisor = eccDivisors[errorCorrectionLevel];

    // Total number of data bits available in the codewords (cooked: after ecc and remainder)
    size_t dataCapacity = ((QRTINY_TOTAL_CAPACITY / 8) - (size_t)eccCodewords) * 8;

    int spareCapacity = (int)dataCapacity - (int)payloadLength;
    if (spareCapacity < 0) return false;  // Does not fit

    // --- Generate final codewords ---
    // Write data segments
    bitPosition = payloadLength;

    // Add terminator 4-bit (0b0000)
    remaining = dataCapacity - bitPosition;
    if (remaining > 4) remaining = 4;
    bitPosition += QrTinyBufferAppend(buffer, bitPosition, QRTINY_MODE_INDICATOR_TERMINATOR, remaining);

    // Round up to a whole byte
    bits = (8 - (bitPosition & 7)) & 7;
    remaining = dataCapacity - bitPosition;
    if (remaining > bits) remaining = bits;
    bitPosition += QrTinyBufferAppend(buffer, bitPosition, 0, remaining);

    // Fill any remaining data space with padding
    while ((remaining = dataCapacity - bitPosition) > 0)
    {
        #define QRTINY_PAD_CODEWORDS 0xec11 // Pad codewords 0b11101100=0xec 0b00010001=0x11
        if (remaining > 16) remaining = 16;
        bitPosition += QrTinyBufferAppend(buffer, bitPosition, QRTINY_PAD_CODEWORDS >> (16 - remaining), remaining);
    }

    // --- Calculate ECC at end of codewords ---
    // Calculate ECC for the block -- write all consecutively after the data (no interleave required for V1)
    QrTinyRSRemainder(buffer, dataCapacity / 8, eccDivisor, eccCodewords, buffer + (QRTINY_TOTAL_CAPACITY - ((size_t)8 * eccCodewords)) / 8);
    return true;
}

int QrTinyModuleGet(uint8_t *buffer, uint16_t formatInfo, int x, int y)
{
  bool mask;
    int type = QrTinyIdentifyModule(x, y, formatInfo);
    if (type == QRTINY_MODULE_DATA)
    {
        int index = QrTinyIdentifyIndex(x, y);
        type = (buffer[index >> 3] & (1 << (index & 7))) ? 1 : 0;
        mask = QrTinyCalculateMask(formatInfo, x, y);
        if (mask) type ^= 1;
    }
    return type;
}







void delay(unsigned int count) {
    volatile unsigned int i;
    volatile unsigned int dummy = 1;

    for (i = 0; i < count; ++i) {
        dummy = dummy * 3;  
    }
}



void main(void) {
    unsigned char selected_sprite = 0;
    unsigned char sprite_temp[SPRITE_HEIGHT * BYTES_PER_ROW];
    const char* URLstrings[8] = {
        "sprite1text", "sprite2text", "sprite3text", "sprite4text",
        "sprite5text", "sprite6text", "sprite7text", "sprite8text"
    };
    int sprite_x[8] = {30, 60, 90, 120, 150, 180, 210, 240};
    unsigned char sprite_y[8] = {220, 220, 220, 220, 220, 220, 220, 220};
    unsigned char bgcoll;
    uint8_t buffer[QRTINY_BUFFER_SIZE];
    uint16_t formatInfo = QRTINY_FORMATINFO_MASK_000_ECC_LOW;
    size_t payloadLength;
    bool result;
    int row, col, i;
    int current_sprite = 0;
    unsigned char toggle_state = 0;
    int delay_counter = 0;
    int oldspritex = 0;
    int oldspritey = 0;

    VIC.spr_color[0] = COLOR_GREEN;
    VIC.spr_color[1] = COLOR_RED;
    VIC.spr_color[2] = COLOR_WHITE;
    VIC.spr_color[3] = COLOR_YELLOW;
    VIC.spr_color[4] = COLOR_BROWN;
    VIC.spr_color[5] = COLOR_BLACK;
    VIC.spr_color[6] = COLOR_CYAN;
    VIC.spr_color[7] = COLOR_PURPLE;

    VIC.spr_ena = 0x00;

    while (1) {
        /* Generate one sprite per frame until all are drawn */
        if (current_sprite < 8) {
            memset((void*)0x0400, 0x20, 1000); /* clear screen */
            putchar(19); /* cursor home */
            printf("generating sprite %d", current_sprite + 1);

            memset(sprite_temp, 0, sizeof(sprite_temp));
            payloadLength = 0;
            payloadLength += QrTinyWriteAlphanumeric(buffer, payloadLength, URLstrings[current_sprite]);
            result = QrTinyGenerate(buffer, payloadLength, formatInfo);

            if (result) {
                for (row = 0; row < SPRITE_HEIGHT; row++) {
                    for (col = 0; col < SPRITE_WIDTH; col++) {
                        int module = QrTinyModuleGet(buffer, formatInfo, col, row);
                        if (module) {
                            int byteIndex = row * BYTES_PER_ROW + (col / 8);
                            int bitIndex = 7 - (col % 8);
                            sprite_temp[byteIndex] |= (1 << bitIndex);
                        }
                    }
                }
            }

            memcpy((char*)(0x3800 + (current_sprite * 64)), sprite_temp, sizeof(sprite_temp));
            // POKE(0x400 + 0x3f8 + current_sprite, (0x3800 + (current_sprite * 64)) / 64);
            *((unsigned char*)(0x0400 + 0x03F8 + current_sprite)) = (0x3800 + (current_sprite * 64)) / 64;
            VIC.spr_pos[current_sprite].x = sprite_x[current_sprite];
            VIC.spr_pos[current_sprite].y = sprite_y[current_sprite];
            VIC.spr_ena |= (1 << current_sprite); /* enable sprite */
            current_sprite++;
        } else {
          memset((void*)0x0400, 0x20, 1000); /* clear screen */
            /* Delay loop counting frames (~1 second) */
            delay_counter++;
            if (delay_counter >= 60) {
                delay_counter = 0;

                if (toggle_state == 0) {
                    /* Turn big_mode ON for selected sprite */
                    oldspritex = sprite_x[selected_sprite];
                    oldspritey = sprite_y[selected_sprite];
                    sprite_x[selected_sprite] = 80;
                    sprite_y[selected_sprite] = 80;

                    /* Clear all big bits first */
                    *((volatile unsigned char*)0xD017) &= 0x00;
                    *((volatile unsigned char*)0xD01D) &= 0x00;

                    /* Enable big sprite bits for selected sprite */
                    *((volatile unsigned char*)0xD017) |= (1 << selected_sprite);
                    *((volatile unsigned char*)0xD01D) |= (1 << selected_sprite);

                } else {
                    /* Turn big_mode OFF for selected sprite */
                    sprite_x[selected_sprite] = oldspritex;
                    sprite_y[selected_sprite] = oldspritey;

                    /* Clear all big bits */
                    *((volatile unsigned char*)0xD017) &= 0x00;
                    *((volatile unsigned char*)0xD01D) &= 0x00;

                    /* Advance to next sprite */
                    selected_sprite++;
                    if (selected_sprite >= 8) selected_sprite = 0;
                }

                toggle_state = !toggle_state;
            }
        }

        waitvsync();

        for (i = 0; i < 8; i++) {
            VIC.spr_pos[i].x = sprite_x[i];
            VIC.spr_pos[i].y = sprite_y[i];
        }

        VIC.spr_hi_x = 0;
        for (i = 0; i < 8; i++) {
            if (sprite_x[i] & 0x100) {
                VIC.spr_hi_x |= (1 << i);
            }
        }

        bgcoll = VIC.spr_bg_coll;
        VIC.spr_color[0] = (bgcoll & 1) ? COLOR_YELLOW : COLOR_GREEN;
    }
}
