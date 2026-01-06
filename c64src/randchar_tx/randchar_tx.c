
#include <conio.h>
#include <stdio.h>
#include <stdlib.h>
#include <peekpoke.h>
#include <string.h>
#include <c64.h>
#include <cbm_petscii_charmap.h>


//#link "common.c"

const unsigned char start_seq[] = { '#', 0 };



#define ACIA_BASE   0xDE00
#define ACIA_DATA   (*(volatile unsigned char *)(ACIA_BASE))
#define ACIA_STATUS (*(volatile unsigned char *)(ACIA_BASE + 1))
#define ACIA_CMD    (*(volatile unsigned char *)(ACIA_BASE + 2))
#define ACIA_CTRL   (*(volatile unsigned char *)(ACIA_BASE + 3))

void init_acia(void) {
    ACIA_CMD = 0x0B;   /* No parity, 8N1, RTS low, TX enabled */
    ACIA_CTRL = 0x0C;  /* 9600 baud, no interrupts */
}


void send_string(const char* s) {
    while (*s) {

        ACIA_DATA = *s++;

        /* crude delay loop to space characters */
        {
            volatile int d;
            for (d = 0; d < 7000; ++d) {
                /* delay */
            }
        }
    }
}

int main(void) {
    clrscr();
    cputs("SwiftLink TX: Sending test pattern...\n\r");

    init_acia();
    send_string("a");
    send_string("#");
    send_string("#");
    send_string("#");
    cputs("Start pattern sent...\n\r");
    send_string("TEST PHRASE");
    cputs("test phrase sent...\n\r");
    send_string("$$$");
    cputs("end...\n\r");

    cputs("Done.\n\r");

    while (1) {
        /* halt */
    }

    return 0;
}
