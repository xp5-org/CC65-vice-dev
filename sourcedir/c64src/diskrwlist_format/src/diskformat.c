#include <cbm.h>
#include <stdio.h>
#include <string.h>

void format_disk(unsigned int device, const char *label, const char *id) {
    unsigned char cmd[64];
    char status[64];
    int bytes;
    int ptr = 0;
    int i;

    /* Build: N0:LABEL,ID */
    cmd[ptr++] = 0x4E; /* N */
    cmd[ptr++] = 0x30; /* 0 */
    cmd[ptr++] = 0x3A; /* : */

    /* Copy label */
    for (i = 0; label[i] != '\0' && ptr < 40; ++i) {
        cmd[ptr++] = label[i];
    }

    cmd[ptr++] = 0x2C; /* , */

    /* Copy ID */
    for (i = 0; id[i] != '\0' && ptr < 60; ++i) {
        cmd[ptr++] = id[i];
    }

    cmd[ptr] = '\0'; /* Null terminator for cbm_open */

    if (cbm_open(15, device, 15, (char*)cmd) != 0) {
        printf("error: device %u not present\n", device);
        return;
    }

    printf("formatting %u with label %s...\n", device, label);

    /* Blocks until format is complete */
    bytes = cbm_read(15, status, sizeof(status) - 1);
    if (bytes > 0) {
        status[bytes] = '\0';
        printf("status: %s\n", status);
    }

    cbm_close(15);
}

int main(void) {
    format_disk(8, "itworks", "01");
    // format_disk(9, "BACKUP", "02");
    
    return 0;
}