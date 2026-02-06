#include <tgi.h>
#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <conio.h>
#include "qrcodegen.h"
#include <cbm.h>
#include <string.h>

#define COLOR_BACK      TGI_COLOR_WHITE
#define COLOR_FORE      TGI_COLOR_BLACK


void drawQr(const uint8_t qrcode[]) {
    int size;
    int x, y;
    int scale;
    int offset_x, offset_y;

    size = qrcodegen_getSize(qrcode);
    scale = 2;      /* Make each QR module 2x2 pixels */
    offset_x = 10;  /* Margin from left */
    offset_y = 10;  /* Margin from top */

    for (y = 0; y < size; y++) {
        for (x = 0; x < size; x++) {
            if (qrcodegen_getModule(qrcode, x, y)) {
                /* Draw a block based on the scale */
                int sx, sy;
                for (sy = 0; sy < scale; sy++) {
                    for (sx = 0; sx < scale; sx++) {
                        tgi_setpixel(offset_x + x * scale + sx, 
                                     offset_y + y * scale + sy);
                    }
                }
            }
        }
    }
}


#include <cbm.h>



#include <conio.h>
#include <stdio.h>
#include <time.h>

int main(void) {
    static const unsigned char Palette[2] = { TGI_COLOR_WHITE, TGI_COLOR_BLACK };
    clock_t start, end;
    long ticks;
    static uint8_t qrcode[qrcodegen_BUFFER_LEN_MAX];
    static uint8_t tempBuffer[qrcodegen_BUFFER_LEN_MAX];
    const char *digits = "314159265358979323asdasdsadsdasdsadsadsadsdasdsadsadsadsdasdsadsads";
    bool ok;

    printf("status: testing numeric encoding...\n");
    printf("input: %s\n", digits);
    start = clock();
    /* Generate the QR code in memory */
    ok = qrcodegen_encodeText(digits, tempBuffer, qrcode,
        qrcodegen_Ecc_MEDIUM, 1, qrcodegen_VERSION_MAX, 
        qrcodegen_Mask_AUTO, true);
    
    
    end = clock();
    ticks = (long)(end - start);
    printf("QRCODETIME: %ld\n", ticks / 60);


    

    if (ok) {
        printf("qrgensuccess\n");
        *(unsigned char*)198 = 0;
        while (!kbhit()) { }
        tgi_install (tgi_static_stddrv); //load tgi driver into mem
        tgi_init ();   // init tgi driver
        tgi_setpalette (Palette);
        tgi_clear ();  //clear screen



        // printf("qr size: %d modules\n", qrcodegen_getSize(qrcode));
      drawQr(qrcode);
    } else {
        printf("qrgenfailed: failed to generate qr\n");
    }
    *(unsigned char*)198 = 0;
    *(unsigned char*)198 = 0;
    while (!kbhit()) { }
    *(unsigned char*)198 = 0;
    waitvsync();
    *(unsigned char*)198 = 0;
    tgi_uninstall (); //unload driver
    return 0;
}
