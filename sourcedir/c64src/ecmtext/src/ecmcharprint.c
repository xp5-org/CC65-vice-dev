#include <c64.h>
#include <stdlib.h>

void main() {
    unsigned int i;
    unsigned char char_base;
    unsigned char bg_choice;
    unsigned char *screen = (unsigned char*)0x0400;
    unsigned char *color_ram = (unsigned char*)0xD800;

    *((unsigned char*)0xD011) |= 0x40;

    *((unsigned char*)0xD021) = COLOR_BLACK;
    *((unsigned char*)0xD022) = COLOR_RED;
    *((unsigned char*)0xD023) = COLOR_GREEN;
    *((unsigned char*)0xD024) = COLOR_BLUE;

    for (i = 0; i < 1000; i++) {
        bg_choice = rand() % 4;
        
        char_base = rand() % 36;
        if (char_base < 26) {
            char_base += 1;
        } else {
            char_base += 12;
        }

        screen[i] = (bg_choice << 6) | (char_base & 0x3F);

        color_ram[i] = rand() % 16;
    }

    while (1);
}