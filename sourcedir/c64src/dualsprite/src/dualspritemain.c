#include <stdlib.h>
#include <string.h>
#include <conio.h>




unsigned char SPRITE_LEFT[64] = {
0xF0, 0x00, 0x18, 0xF0, 0x00, 0x18,
0xFF, 0xC0, 0x08, 0xFF, 0xF0, 0x88,
0xE3, 0xF0, 0x88, 0xE3, 0xF0, 0x80,
0xC3, 0xF1, 0xC0, 0xC3, 0xE1, 0xC0,
0xC3, 0x07, 0xC0, 0xC0, 0x1F, 0xE0,
0xFF, 0xFF, 0xE0, 0xFF, 0xFF, 0xE0,
0xFF, 0xFF, 0xF8, 0xFF, 0xFF, 0xF8,
0xF8, 0x00, 0x00, 0x80, 0x01, 0xF8,
0x80, 0x01, 0xF8, 0xF0, 0x00, 0x00,
0xFF, 0xF8, 0x00, 0x00, 0x00, 0x00,
};


unsigned char SPRITE_RIGHT[64] = {
0xFC, 0x00, 0xF8, 0xF8, 0x00, 0x18,
0xF0, 0xFE, 0x08, 0xE1, 0xFF, 0x80,
0xC3, 0x1F, 0x80, 0xC6, 0x1F, 0x80,
0x8E, 0x1F, 0x08, 0x1E, 0x3F, 0x18,
0x3E, 0x18, 0x38, 0x3E, 0x00, 0xF8,
0x7F, 0xFF, 0xF8, 0xFF, 0xFF, 0xF8,
0xFF, 0xFF, 0xF8, 0xFF, 0xFF, 0xF8,
0x00, 0x03, 0xF8, 0xC0, 0x00, 0x38,
0xE0, 0x00, 0x38, 0x00, 0x01, 0xF8,
0x07, 0xFF, 0xF8, 0x00, 0x00, 0x00,
};





void do_nothing(void) {
    volatile unsigned int i;
    for (i = 0; i < 300; i++) {
       ; // empty body, just wastes CPU cycles
    }
}

void do_nothing_videodelay(void) {
    volatile unsigned int i;
    for (i = 0; i < 6; i++) {
waitvsync();
    }
}


unsigned int x = 20; // start pos needs to be boundry pair to align with corner
unsigned int y = 50;
signed char dx = 1;   // horizontal movement (+1 or -1)
signed char dy = 1;   // vertical movement (+1 or -1)



void move_sprites(void) {
    x += dx;
    y += dy;

    if (x == 20 || x >= 305) dx = -dx;
    if (y == 50 || y >= 230) dy = -dy;


    VIC.spr_pos[0].x = (unsigned char)x;

    if (x & 0x100) {
        (*(unsigned char*)0xD010) |= 0x01;
    } else {
        (*(unsigned char*)0xD010) &= ~0x01;
    }

    VIC.spr_pos[1].x = (unsigned char)(x + 21);

    if ((x + 21) & 0x100) {
        (*(unsigned char*)0xD010) |= 0x02;
    } else {
        (*(unsigned char*)0xD010) &= ~0x02;
    }

    VIC.spr_pos[0].y = (unsigned char)y;
    VIC.spr_pos[1].y = (unsigned char)y;
}


int check_corner_bounce(int old_dx, int old_dy, int dx, int dy) {
    if (dx != old_dx && dy != old_dy) return 1;
    return 0;
}





void load_sprites(void) {
  // sprite pointer base 0x07F8
    memcpy((char*)0x3800, SPRITE_LEFT, 64);
    memcpy((char*)0x3840, SPRITE_RIGHT, 64);
   *((unsigned char *)(0x07F8 + 0)) = 0xE0;
   *((unsigned char *)(0x07F8 + 1)) = 0xE1;
    VIC.spr_ena = 3;
  
}

void flashborder(unsigned char backgroundcolor) {
    unsigned char i;
    for (i = 0; i < 8; i++) {
        *(unsigned char*)0xd020 = (backgroundcolor + 11 + i) & 0x0F;
do_nothing_videodelay();
    }
    for (i = 8; i > 0; i--) {
        *(unsigned char*)0xd020 = (backgroundcolor + 11 + i) & 0x0F;
do_nothing_videodelay();
    }
    *(unsigned char*)0xd020 = (backgroundcolor + 11) & 0x0F;
}




int main(void)
{
unsigned int oldx = 50;
unsigned int oldy = 70;
unsigned char backgroundcolor;

load_sprites();
clrscr();
  
  
backgroundcolor = 6;
*(unsigned char*)0xd021 = backgroundcolor;
VIC.spr_color[0] = backgroundcolor+1;
VIC.spr_color[1] = backgroundcolor+1;
*(unsigned char*)0xd020 = backgroundcolor-5; //border color  

while (1) {
  
    signed char old_dx = dx;
    signed char old_dy = dy;
    move_sprites();
    do_nothing();

    if (check_corner_bounce(old_dx, old_dy, dx, dy)) {
        unsigned char backgroundcolor = *(unsigned char*)0xd021;
        backgroundcolor = (backgroundcolor + 1) & 0x0F;
        *(unsigned char*)0xd021 = backgroundcolor;
        VIC.spr_color[0] = (backgroundcolor + 1) & 0x0F;
        VIC.spr_color[1] = (backgroundcolor + 1) & 0x0F;
        *(unsigned char*)0xd020 = (backgroundcolor + 11) & 0x0F; // border = bg-5
      flashborder(backgroundcolor);
    }




   
}

    return EXIT_SUCCESS;
}


