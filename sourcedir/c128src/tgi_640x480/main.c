#include <stdio.h>
#include <c128.h>
#include <tgi.h>
#include <conio.h>

extern char c128_640x480;

static unsigned char palette[2] = {
    TGI_COLOR_BLACK,
    TGI_COLOR_WHITE
};



#define VDC_ADDR (*(volatile unsigned char*)0xD600)
#define VDC_DATA (*(volatile unsigned char*)0xD601)

void vdc_write(unsigned char reg, unsigned char val) {
    while (!(VDC_ADDR & 0x80));
    VDC_ADDR = reg;
    while (!(VDC_ADDR & 0x80));
    VDC_DATA = val;
}

void fast_vdc_gradient(unsigned int vram_base) {
    unsigned int x_byte, y;
    unsigned char bits, b, intensity, step_v, counter;
    unsigned int v_row_start;
    unsigned int v_running;

    v_row_start = 0;
    step_v = 0;

    vdc_write(18, (unsigned char)(vram_base >> 8));
    vdc_write(19, (unsigned char)(vram_base & 0xff));
    
    while (!(VDC_ADDR & 0x80));
    VDC_ADDR = 31;

    for (y = 0; y < 480; ++y) {
        counter = step_v;
        v_running = v_row_start;
        
        for (x_byte = 0; x_byte < 80; ++x_byte) {
            bits = 0;
            
            /* Unrolling the bit loop removes loop overhead and shifts */
            for (b = 0; b < 8; ++b) {
                /* (v >> 5) is the same as (v / 32) */
                intensity = (unsigned char)(v_running >> 5);
                
                bits <<= 1;
                if ((counter & 31) < intensity) {
                    bits |= 1;
                }
                
                counter += 3;
                v_running++;
            }
            
            while (!(VDC_ADDR & 0x80));
            VDC_DATA = bits;
        }
        step_v += 5;
        v_row_start += 1;
    }
}


int main(void)
{
int x, y, v, intensity, step_v;
    tgi_install(&c128_640x480);

    // https://cc65.github.io/doc/funcref.html#fast
    fast(); // c128 speed arg

    tgi_init();
    tgi_clear();

    tgi_setpalette(palette);
    tgi_clear();

    tgi_setcolor(1);

    tgi_line(100, 100, 540, 100);
    tgi_line(540, 100, 540, 380);
    tgi_line(540, 380, 100, 380);
    tgi_line(100, 380, 100, 100);

    // custom method - faster gradient fill
    fast_vdc_gradient(0x0000);


// TGI - slow gradient fill
 //   for (y = 0; y < 480; ++y) {
 //           step_v = y * 5;
 //           for (x = 0; x < 640; ++x) {
 //               v = x + y;
 //               intensity = v >> 5;
 //               if (((x * 3 + step_v) & 31) < intensity) {
 //                   tgi_setpixel(x, y);
 //               }
 //           }
 //       }
//
//
    while (!kbhit())
    ;

    tgi_done();
    return 0;
}
