#include <cbm.h>
#include <string.h>
//#include <stdio.h>

int main(void) {
    if (cbm_open(4, 4, 0, "") == 0) {
        cbm_write(4, "test1", 5);
        cbm_write(4, "\r", 1);
        cbm_write(4, "test2", 5);
        cbm_write(4, "\r", 1);
        cbm_close(4);
    }

   // printf("hmm");
    return 0;
}
