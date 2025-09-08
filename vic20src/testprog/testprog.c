#include <stdio.h>
#include <vic20.h>
#include <conio.h>


int main(void) {
    int x, y;

    for (y = 0; y < 21; y++) {
        for (x = 0; x < 21; x++) {
            if ((x + y) % 2 == 0) {
                putchar(166);
            } else {
                putchar(160);
            }
        }
        putchar('\r');
        putchar('\n');
    }

    while (1) {}
    return 0;
}