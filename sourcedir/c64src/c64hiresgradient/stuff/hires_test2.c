#include <stdlib.h>


// this is random color example

#define BITMAP  ((unsigned char*)0x4000)
#define SCREEN  ((unsigned char*)0x6000)

void init_hires(void) {
    unsigned int i;
    unsigned char fg;
    unsigned char v;

    v = *(unsigned char*)0xDD00;
    v &= 0xFC;
    v |= 0x02;
    *(unsigned char*)0xDD00 = v;

    *(unsigned char*)0xD011 = 0x3B;
    *(unsigned char*)0xD016 = 0x08;
    *(unsigned char*)0xD018 = 0x80;
    *(unsigned char*)0xD021 = 0x00;

    for (i = 0; i < 1000; i++) {
        fg = (rand() % 15) + 1;
        SCREEN[i] = fg << 4;
    }

    for (i = 0; i < 8000; i++) {
        BITMAP[i] = 0;
    }
}

void main(void) {
    unsigned char master_pattern[8][40];
    unsigned int x, y, byte_x, row;
    unsigned long t;
    unsigned char r, threshold;

    init_hires();

    for (y = 0; y < 8; y++) {
        for (byte_x = 0; byte_x < 40; byte_x++) {
            unsigned char bits = 0;
            for (x = 0; x < 8; x++) {
                unsigned int pixel_x = (byte_x << 3) + x;
                t = 319 - pixel_x;
                threshold = (unsigned char)((t * t * 255UL) / 101761UL);
                r = (unsigned char)(rand() & 255);
                if (r < threshold) {
                    bits |= (1 << (7 - x));
                }
            }
            master_pattern[y][byte_x] = bits;
        }
    }

    for (row = 0; row < 25; row++) {
        unsigned int tile_row_offset = row * 320;
        for (y = 0; y < 8; y++) {
            unsigned int line_offset = tile_row_offset + y;
            for (byte_x = 0; byte_x < 40; byte_x++) {
                BITMAP[line_offset + (byte_x << 3)] = master_pattern[y][byte_x];
            }
        }
    }

    while (1);
}