#include <cbm_petscii_charmap.h>
#include <cbm.h>
#include <stdio.h>
#include <string.h>

#define MAX_FILES 32 

struct file_info {
    char name[17];
    char type[4];
    unsigned int size;
};

static struct file_info file_list[MAX_FILES];
static int total_files = 0;
static char full_name[32];
static char io_buffer[256];


int list_files(unsigned int device) {
    unsigned char c;
    unsigned char link[2];
    unsigned char low;
    unsigned char high;
    int i;
    int entry_count;
    unsigned int line_size;
    
    entry_count = 0;

    if (cbm_open(15, device, 0, "$") != 0) {
        return 0;
    }

    /* Read the initial 2-byte load address (discard) */
    cbm_read(15, link, 2);

    /* Main Directory Loop */
    while (1) {
        /* Read the Link Pointer (2 bytes) */
        /* If we can't read 2 bytes, we are done */
        if (cbm_read(15, link, 2) != 2) break;
        
        /* If Link is 00 00, it's the end of the program/directory */
        if (link[0] == 0 && link[1] == 0) break;

        /* Read File Size (Line Number) */
        cbm_read(15, &low, 1);
        cbm_read(15, &high, 1);
        line_size = low + (high * 256);

        /* CHECK 1: Skip Header (Line number 0) */
        if (line_size == 0) {
            do { cbm_read(15, &c, 1); } while (c != 0);
            continue;
        }

        /* Scan for the first quote */
        do {
            cbm_read(15, &c, 1);
        } while (c != '"' && c != 0);

        /* CHECK 2: Detect "BLOCKS FREE" line */
        /* If we hit EOL (0) without finding a quote, it's the footer/blocks free line */
        if (c == 0) {
            /* We already consumed the 0, so just move to next line */
            continue;
        }

        /* Stop if we've hit our struct limit */
        if (entry_count >= MAX_FILES) {
            /* Consume rest of this line so we don't leave the buffer dirty, then stop */
            while (c != 0) cbm_read(15, &c, 1);
            break;
        }

        /* Store Size */
        file_list[entry_count].size = line_size;

        /* Parse Filename */
        i = 0;
        while (i < 16) {
            cbm_read(15, &c, 1);
            if (c == '"' || c == 0) break;
            file_list[entry_count].name[i] = c;
            i++;
        }
        file_list[entry_count].name[i] = '\0';

        /* Parse File Type */
        /* Skip spaces after the closing quote */
        do {
            cbm_read(15, &c, 1);
        } while (c == ' ' && c != 0);
        
        file_list[entry_count].type[0] = c;
        cbm_read(15, &file_list[entry_count].type[1], 1);
        cbm_read(15, &file_list[entry_count].type[2], 1);
        file_list[entry_count].type[3] = '\0';

        /* Consume the rest of the line (garbage or protection flags) until 0x00 */
        while (c != 0) {
            if (cbm_read(15, &c, 1) == 0) break;
        }

        entry_count++;
    }
    cbm_close(15);
    return entry_count;
}


void process_file_data(struct file_info *list, int count) {
    int i;
    for (i = 0; i < count; i++) {
        printf("OBJ[%d] -> NAME:%s TYPE:%s SIZE:%u\n", 
                i, list[i].name, list[i].type, list[i].size);
    }
}


void save_to_disk(const char *name, const char *type_suffix, unsigned int fileid, unsigned int diskdeviceid, const char *data) {
    strcpy(full_name, name);
    strcat(full_name, type_suffix);

    if (cbm_open(fileid, diskdeviceid, 2, full_name) == 0) {
        cbm_write(fileid, data, strlen(data));
        cbm_close(fileid);
        printf("saved: %s\n", full_name);
    } else {
        printf("save error: %s\n", full_name);
    }
}


void read_from_disk(const char *name, const char *type_suffix, unsigned int fileid, unsigned int device) {
    int bytes_read;
    strcpy(full_name, name);
    strcat(full_name, type_suffix);

    if (cbm_open(fileid, device, 2, full_name) == 0) {
        bytes_read = cbm_read(fileid, io_buffer, sizeof(io_buffer) - 1);
        if (bytes_read >= 0) {
            io_buffer[bytes_read] = '\0';
            printf("read %s: %s\n", name, io_buffer);
        }
        cbm_close(fileid);
    } else {
        printf("error reading %s\n", full_name);
    }
}





void format_disk(unsigned int device, const char *label, const char *id) {
    char cmd[64];
    char status[64];
    int bytes;

    /* Ensure ID is exactly 2 chars; pad with 0 if needed */
    char fixed_id[3];
    if (strlen(id) == 1) {
        sprintf(fixed_id, "0%s", id);
    } else {
        strncpy(fixed_id, id, 2);
        fixed_id[2] = '\0';
    }

    /* Command syntax: N0:NAME,ID */
    sprintf(cmd, "N0:%s,%s", label, fixed_id);

    /* Open secondary address 15 (command channel) */
    if (cbm_open(15, device, 15, cmd) != 0) {
        printf("Error: Could not open device %u\n", device);
        return;
    }

    printf("Formatting device %u... (please wait)\n", device);

    /* CRITICAL: Read the error channel. 
       This blocks until the drive is done formatting and 
       returns the status string (e.g., "00, OK, 00, 00") */
    bytes = cbm_read(15, status, sizeof(status) - 1);
    if (bytes > 0) {
        status[bytes] = '\0';
        printf("Drive Status: %s\n", status);
    }

    cbm_close(15);
}


int main(void) {
    unsigned int fileid = 2;
    unsigned int diskdeviceid = 8;

    save_to_disk("8myPRGfile", ",p,w", fileid, diskdeviceid, "PRG file contents");
    save_to_disk("8mySEQfile", ",s,w", fileid, diskdeviceid, "SEQ file contents");
    save_to_disk("8myUSRfile", ",u,w", fileid, diskdeviceid, "USR file contents");
    
    total_files = list_files(diskdeviceid);
    process_file_data(file_list, total_files);

    read_from_disk("8myPRGfile", ",p", fileid, diskdeviceid);
    read_from_disk("8mySEQfile", ",s", fileid, diskdeviceid);
    read_from_disk("8myUSRfile", ",u", fileid, diskdeviceid);

    diskdeviceid = 9;
    memset(file_list, 0, sizeof(file_list));
    total_files = 0;
    // test disk 9
    format_disk(9, "MYDISK", "02");
    save_to_disk("9myPRGfile", ",p,w", fileid, diskdeviceid, "PRG file contents");
    save_to_disk("9mySEQfile", ",s,w", fileid, diskdeviceid, "SEQ file contents");
    save_to_disk("9myUSRfile", ",u,w", fileid, diskdeviceid, "USR file contents");

    total_files = list_files(diskdeviceid);
    process_file_data(file_list, total_files);

    printf("test complete\n");
    return 0;
}