#include <vic20.h>
#include <conio.h>
#include <stdlib.h>

int main(void) {
    int x, y;

    clrscr();

    for (y = 0; y < 23; y++) {
        for (x = 0; x < 22; x++) {
            /* 1. Set the active text color (0-7) */
            textcolor(2 + rand() % 28);

            /* 2. Draw the character at coordinate x, y */
            /* The library will now update COLOR_RAM for us */
            cputcxy(x, y, ((x + y) % 2 == 0) ? 166 : 160);
        }
    }

    while (1) {}
    return 0;
}