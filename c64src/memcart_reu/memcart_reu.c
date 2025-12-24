#include <c64.h>
#include <conio.h>
#include <em.h>
#include <stdio.h>

extern char c64_reu;  // symbol from the linked REU driver object

int main(void) {
    unsigned char result = em_install(&c64_reu);

    if (result == 0) {  // EM_ERR_OK is typically 0
        printf("REU driver installed successfully.\n");
    } else {
        printf("Failed to install REU driver, error code: %d\n", result);
    }

    return 0;
}
