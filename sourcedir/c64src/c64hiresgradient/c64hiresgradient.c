#include <stdint.h>
#include <cbm.h>

#define BITMAP_BASE 0x4000
#define SCREEN_BASE 0x6000

static const unsigned int row_offsets[] = {
    0, 320, 640, 960, 1280, 1600, 1920, 2240, 2560, 2880,
    3200, 3520, 3840, 4160, 4480, 4800, 5120, 5440, 5760, 6080,
    6400, 6720, 7040, 7360, 7680
};

static const unsigned char bayer8[8][8] = {
    { 0, 32,  8, 40,  2, 34, 10, 42},
    {48, 16, 56, 24, 50, 18, 58, 26},
    {12, 44,  4, 36, 14, 46,  6, 38},
    {60, 28, 68, 20, 62, 30, 70, 22},
    { 3, 35, 11, 43,  1, 33,  9, 41},
    {51, 19, 59, 27, 49, 17, 57, 25},
    {15, 47,  7, 39, 13, 45,  5, 37},
    {63, 31, 71, 23, 61, 29, 69, 21}
};

static const unsigned char hr_rainbow[] = { 
    0xE6, 0x3E, 0x13, 0xD1, 0x3D, 0xFE, 0x7F, 0xAF, 0x4A, 0x04, 0x60,
    0xE6, 0x3E, 0x13, 0xD1, 0x3D, 0xFE, 0x7F, 0xAF, 0x4A, 0x04, 0x60 
};



void gradient() {
    unsigned int x_tile, y_pix, row;
    unsigned int base_intensity, i;
    unsigned char bits, gy_idx;
    unsigned char* ptr;
    const unsigned char* bayer_row;

    for (row = 0; row < 25; ++row) {
        for (y_pix = 0; y_pix < 8; ++y_pix) {
            gy_idx = y_pix; 
            bayer_row = bayer8[gy_idx];
            base_intensity = ((row << 3) + y_pix);
            ptr = (unsigned char*)(BITMAP_BASE + row_offsets[row] + y_pix);

            for (x_tile = 0; x_tile < 40; ++x_tile) {
                bits = 0;
                i = base_intensity + (x_tile << 3);
                if (((i    ) >> 3) > bayer_row[0]) bits |= 0x80;
                if (((i + 1) >> 3) > bayer_row[1]) bits |= 0x40;
                if (((i + 2) >> 3) > bayer_row[2]) bits |= 0x20;
                if (((i + 3) >> 3) > bayer_row[3]) bits |= 0x10;
                if (((i + 4) >> 3) > bayer_row[4]) bits |= 0x08;
                if (((i + 5) >> 3) > bayer_row[5]) bits |= 0x04;
                if (((i + 6) >> 3) > bayer_row[6]) bits |= 0x02;
                if (((i + 7) >> 3) > bayer_row[7]) bits |= 0x01;

                *ptr = bits;
                ptr += 8;
            }
        }
    }
}




void rotate_hires_colors(unsigned char offset)
{
    unsigned char x, y;
    unsigned char row_idx, col_idx;
    unsigned char *scr_ptr = (unsigned char*)SCREEN_BASE;
    unsigned char v;

    offset %= 11;

    row_idx = offset;

    for (y = 0; y < 25; ++y) {
        col_idx = row_idx;

        for (x = 0; x < 40; ++x) {
            v = *scr_ptr;
            v = (v & 0xF0) | (hr_rainbow[col_idx] & 0x0F);
            *scr_ptr++ = v;

            col_idx++;
            if (col_idx == 11)
                col_idx = 0;
        }
        row_idx++;
        if (row_idx == 11)
            row_idx = 0;
    }
}




int main() {
    unsigned int i;
    int frame;
    
    *(unsigned char*)0xD011 = 0x3B;  
    *(unsigned char*)0xD016 = 0x08;  
    *(unsigned char*)0xDD00 = 0x02; 
    *(unsigned char*)0xD018 = 0x80; 

    for (i = 0; i < 1000; i++) {
        ((unsigned char*)SCREEN_BASE)[i] = 0x10; // bg color gray
    }

    *(unsigned char*)0xD020 = 0x00; //border color

    gradient();
  
    while(1) {
    rotate_hires_colors(frame);
    frame++;
    if (frame >= 11) frame = 0;
    }

    return 0;
}