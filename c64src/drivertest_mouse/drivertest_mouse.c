#include <c64.h>
#include <conio.h>
#include <mouse.h>
#include <stdio.h>

extern char c64_1351;

int main(void) {
    unsigned char result;
    struct mouse_info info;

    result = mouse_install(&mouse_def_callbacks, &c64_1351);

    if (result != MOUSE_ERR_OK) {
        printf("Error: %d\n", result);
        return 1;
    }

    clrscr();
    printf("Press key to exit\n");
    
    mouse_show();

    while (!kbhit()) {
        mouse_info(&info);

        gotoxy(0, 2);
        printf("X: %3d  Y: %3d  ", info.pos.x, info.pos.y);

        gotoxy(0, 4);
        printf("Buttons: ");
        
        if ((info.buttons & MOUSE_BTN_LEFT) && (info.buttons & MOUSE_BTN_RIGHT)) {
            printf("BOTH  ");
        } else if (info.buttons & MOUSE_BTN_LEFT) {
            printf("LEFT  ");
        } else if (info.buttons & MOUSE_BTN_RIGHT) {
            printf("RIGHT ");
        } else {
            printf("NONE  ");
        }
    }

    mouse_hide();
    mouse_uninstall();
    
    return 0;
}