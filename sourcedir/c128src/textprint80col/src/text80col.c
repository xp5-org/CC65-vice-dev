#include <c128.h>
#include <conio.h>
#include <stdlib.h>

extern unsigned int _heapmemavail(void);

int main(void)
{
    unsigned int free_mem;

    videomode(VIDEOMODE_80COL);
    clrscr();

    free_mem = _heapmemavail();

    cputsxy(0, 0, "HELLO");
    gotoxy(0, 2);
    cprintf("FREE MEMORY: %u BYTES", free_mem);

    cgetc();
    return 0;
}
