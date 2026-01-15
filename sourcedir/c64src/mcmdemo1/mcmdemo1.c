#include <stdint.h>
#include <cbm.h>

#define BITMAP_BASE 0x4000
#define SCREEN_BASE 0x6000

static const unsigned int row_offsets[] = {
    0, 320, 640, 960, 1280, 1600, 1920, 2240, 2560, 2880,
    3200, 3520, 3840, 4160, 4480, 4800, 5120, 5440, 5760, 6080,
    6400, 6720, 7040, 7360, 7680
};




/* Pre-shifted rainbow values: (col << 4) | (col & 0x0F) */
static const unsigned char rainbow_packed[] = { 
    0x66, 0xEE, 0x33, 0xDD, 0x11, 0xCC, 0xBB, 0x44, 0xAA, 0xFF, 0x77,
    0x66, 0xEE, 0x33, 0xDD, 0x11, 0xCC, 0xBB, 0x44, 0xAA, 0xFF, 0x77 
};

/* Raw rainbow values for Color RAM */
static const unsigned char rainbow_raw[] = { 
    0x06, 0x0E, 0x03, 0x0D, 0x01, 0x0C, 0x0B, 0x04, 0x0A, 0x0F, 0x07,
    0x06, 0x0E, 0x03, 0x0D, 0x01, 0x0C, 0x0B, 0x04, 0x0A, 0x0F, 0x07 
};



static const unsigned char rainbow[] = { 6, 14, 3, 13, 1, 12, 11, 4, 10, 15, 7 };

void gradient() {
    unsigned int x_tile, y_pix, row;
    unsigned char bits, intensity, counter, step_v;
    unsigned int v_row_start, v_running;
    unsigned char* ptr_base;
    unsigned char* ptr;

    v_row_start = 0;
    step_v = 0;

    for (row = 0; row < 25; ++row) {
        ptr_base = (unsigned char*)(BITMAP_BASE + row_offsets[row]);
        for (y_pix = 0; y_pix < 8; ++y_pix) {
            counter = step_v;
            v_running = v_row_start;
            ptr = ptr_base + y_pix;
            for (x_tile = 0; x_tile < 40; ++x_tile) {
                bits = 0;
                intensity = (unsigned char)(v_running >> 4);
                
                /* Each bit pair is checked against the same intensity */
                /* If 'on', we set it to %11 to use the Color RAM value */
                if ((counter & 31) < intensity) bits |= 0xC0; 
                counter += 3; v_running++;
                
                if ((counter & 31) < intensity) bits |= 0x30; 
                counter += 3; v_running++;
                
                if ((counter & 31) < intensity) bits |= 0x0C; 
                counter += 3; v_running++;
                
                if ((counter & 31) < intensity) bits |= 0x03; 
                counter += 3; v_running++;
                
                *ptr = bits;
                ptr += 8;
            }
            step_v += 5;
            v_row_start += 1;
        }
    }
}



void rotate_colors(unsigned char offset) {
    unsigned char x, y;
    unsigned char *scr_ptr = (unsigned char*)SCREEN_BASE;
    unsigned char *col_ptr = (unsigned char*)COLOR_RAM;
    unsigned char row_start_idx;
    unsigned char current_idx;

    /* Normalize offset to avoid overflow, though % 11 is still used once here */
    offset %= 11;

    for (y = 0; y < 25; ++y) {
        /* Pre-calculate where this row starts in the rainbow table */
        row_start_idx = (y + offset) % 11;
        
        for (x = 0; x < 40; ++x) {
            /* Use a simple counter that wraps using the double-length table */
            current_idx = row_start_idx + (x % 11);
            
            *scr_ptr++ = rainbow_packed[current_idx];
            *col_ptr++ = rainbow_raw[current_idx];
        }
    }
}



int main() {
    unsigned int x, y, i;
    unsigned char col;
    unsigned int frame;
    __asm__("sei");

    *(unsigned char*)0xDD00 = (*(unsigned char*)0xDD00 & 0xFC) | 0x02;
    *(unsigned char*)0xD018 = 0x80;
    *(unsigned char*)0xD011 = 0x3B;
    *(unsigned char*)0xD016 = 0x18;
    *(unsigned char*)0xD021 = 0x00; 

    for (y = 0; y < 25; y++) {
        for (x = 0; x < 40; x++) {
            i = y * 40 + x;
            
            /* Pick one color for the whole tile to avoid clashing */
            col = rainbow[(x + y) % 11];

            /* Set all 3 multicolor slots to the same color */
            ((unsigned char*)SCREEN_BASE)[i] = (col << 4) | (col & 0x0F);
            ((unsigned char*)0xD800)[i] = (col & 0x0F);
        }
    }

    gradient();
while(1) {
        /* Wait for the raster to reach the bottom of the screen to avoid flickering */
        while (*(volatile unsigned char*)0xD012 < 250);
        rotate_colors(frame++);
    }
    while(1);
    return 0;
}