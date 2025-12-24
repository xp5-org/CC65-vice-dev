#include <stdio.h>
#include <serial.h>

extern char c64_swlink;

int main(void) {
    unsigned char result = ser_install(&c64_swlink);

    if (result == SER_ERR_OK) {
        printf("Serial driver installed successfully.\n");
    } else {
        printf("Failed to install serial driver, error code: %d\n", result);
    }

    return 0;
}
