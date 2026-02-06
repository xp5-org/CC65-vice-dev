#include <cbm.h>
#include <stdio.h>

int main(void) {
    char buf[64];
    int len;

    len = sprintf(buf, "Value: %d\r", 42);

    if (cbm_open(4, 4, 0, "") == 0) {
        cbm_write(4, buf, len);
        cbm_close(4);
    }
    return 0;
}
