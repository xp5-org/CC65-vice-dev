#include <conio.h>
#include <stdio.h>
#include <stdlib.h>
#include <peekpoke.h>
#include <string.h>
#include <c64.h>
#include <cbm_petscii_charmap.h>

#define ACIA_BASE   0xDE00
#define ACIA_DATA   (*(volatile unsigned char *)(ACIA_BASE))
#define ACIA_STATUS (*(volatile unsigned char *)(ACIA_BASE + 1))
#define ACIA_CMD    (*(volatile unsigned char *)(ACIA_BASE + 2))
#define ACIA_CTRL   (*(volatile unsigned char *)(ACIA_BASE + 3))

#define SCREEN_WIDTH 40
#define STATUS_LINE_Y 22

void init_acia(void) {
    ACIA_CMD = 0x0B;
    ACIA_CTRL = 0x0C;
}

void send_string(const char* s) {
    while (*s) {
        ACIA_DATA = *s++;

        {
            volatile int d;
            for (d = 0; d < 7000; ++d) {
                // delay
            }
        }
    }
}

void draw_green_count(unsigned int count) {
    char msg[40];
    unsigned short offset = STATUS_LINE_Y * SCREEN_WIDTH;
    unsigned char i;

    sprintf(msg, "TX Count: %u chars", count);

    for (i = 0; i < SCREEN_WIDTH; ++i) {
        if (msg[i] == '\0') {
            break;
        }
        POKE(0x0400 + offset + i, msg[i]);
        POKE(0xD800 + offset + i, 0x1C); /* green on black */
    }

    for (; i < SCREEN_WIDTH; ++i) {
        POKE(0x0400 + offset + i, ' ');
        POKE(0xD800 + offset + i, 0x1C);
    }
}

int main(void) {
    unsigned int count = 0;

    clrscr();
    cputs("SwiftLink TX: Sending test pattern...\n\r");

    init_acia();

    send_string("a"); //not sure why but have to send a normal char before a # char? 
    send_string("#");
    send_string("#");
    send_string("#");
    cputs("Start pattern sent...\n\r");

    send_string("TEST PHRASE"); count += strlen("TEST PHRASE");
    cputs("test phrase sent...\n\r");

    send_string("$$$");
    cputs("end...\n\r");

    draw_green_count(count);

    cputs("Done.\n\r");

    while (1) {
        /* halt */
    }

    return 0;
}
