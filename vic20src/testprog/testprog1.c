#include <vic20.h>
#include <conio.h>

int main(void) {
    clrscr();
    const char *msg = "Hello world!\r\n";
    while (*msg) {
        cputc(*msg++);
    }
    while (1) {}
    return 0;
}
