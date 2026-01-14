#include <tgi.h>
#include <conio.h>

extern char c128_640x480;

static unsigned char palette[2] = {
    TGI_COLOR_BLACK,
    TGI_COLOR_WHITE
};



int main(void)
{
    tgi_install(&c128_640x480);

    tgi_init();
    tgi_clear();

    tgi_setpalette(palette);
    tgi_clear();

    tgi_setcolor(1);

    tgi_line(100, 100, 540, 100);
    tgi_line(540, 100, 540, 380);
    tgi_line(540, 380, 100, 380);
    tgi_line(100, 380, 100, 100);

    while (!kbhit())
    ;

    tgi_done();
    return 0;
}
