#include <conio.h>
#include <peekpoke.h>
#include <stdlib.h>
#include <string.h>
#include <c64.h>
#include <cbm_petscii_charmap.h>
#include <stdio.h>

#define ACIA_BASE   0xDE00
#define ACIA_DATA   (*(volatile unsigned char *)(ACIA_BASE))
#define ACIA_STATUS (*(volatile unsigned char *)(ACIA_BASE + 1))
#define ACIA_CMD    (*(volatile unsigned char *)(ACIA_BASE + 2))
#define ACIA_CTRL   (*(volatile unsigned char *)(ACIA_BASE + 3))

#define SCREEN_WIDTH 40
#define STATUS_LINE_Y 22
#define MAX_BUFFER 256

/* Globals to reduce stack usage */
static char recv_buffer[MAX_BUFFER];
static char count_str[40];

void print_status(const char* str, unsigned char line) {
    unsigned short offset = line * SCREEN_WIDTH;
    unsigned char i;
    for (i = 0; i < SCREEN_WIDTH; i++) {
        if (str[i] == '\0') {
            break;
        }
        POKE(0x0400 + offset + i, str[i]);
        POKE(0xD800 + offset + i, 0x15); /* White on blue */
    }
    for (; i < SCREEN_WIDTH; i++) {
        POKE(0x0400 + offset + i, ' ');
        POKE(0xD800 + offset + i, 0x15);
    }
}

void init_acia(void) {
    POKE(ACIA_BASE + 2, 0x0B);
    POKE(ACIA_BASE + 3, 0x0C);
}

int main(void) {
    unsigned char rx_ready;
    unsigned char rx_char;

    unsigned int recv_index = 0;
    unsigned int recv_count = 0;

    unsigned char start_seq_count = 0;
    unsigned char stop_seq_count = 0;
    unsigned char recording = 0;

    clrscr();
    cputs("Swiftlink RX Demo\n\r");
    init_acia();

    print_status("Waiting for ### to start recording...", STATUS_LINE_Y);
    print_status("", STATUS_LINE_Y + 1);

    while (1) {
        rx_ready = (PEEK(ACIA_BASE + 1) & 0x08) ? 1 : 0;

        if (rx_ready) {
            rx_char = PEEK(ACIA_BASE);

            if (rx_char == 0x1C) {
                continue;
            }

            if (!recording) {
                if (rx_char == '#') {
                    start_seq_count++;
                    if (start_seq_count == 3) {
                        recording = 1;
                        recv_index = 0;
                        recv_count = 0;
                        stop_seq_count = 0;
                        print_status("Recording started...", STATUS_LINE_Y);
                        print_status("", STATUS_LINE_Y + 1);
                    }
                } else {
                    start_seq_count = 0;
                }
            } else {
                if (recv_index < MAX_BUFFER - 1) {
                    recv_buffer[recv_index++] = rx_char;
                    recv_count++;
                }

                if (rx_char == '$') {
                    stop_seq_count++;
                    if (stop_seq_count == 3) {
                        recv_index -= 3;
                        if (recv_index > MAX_BUFFER - 1) {
                            recv_index = MAX_BUFFER - 1;
                        }
                        recv_buffer[recv_index] = '\0';

                        print_status("Received:", STATUS_LINE_Y);
                        {
                            unsigned int delay;
                            for (delay = 0; delay < 500; delay++) {}
                        }
                        print_status(recv_buffer, STATUS_LINE_Y);

                        snprintf(count_str, sizeof(count_str), "Count: %u chars", (recv_count >= 3) ? recv_count - 3 : 0);

                        print_status(count_str, STATUS_LINE_Y + 1);

                        recording = 0;
                        start_seq_count = 0;
                        stop_seq_count = 0;
                        recv_index = 0;
                        recv_count = 0;
                    }
                } else {
                    stop_seq_count = 0;
                }

                if (recv_index >= MAX_BUFFER - 1) {
                    print_status("Buffer overflow! Resetting.", STATUS_LINE_Y);
                    print_status("", STATUS_LINE_Y + 1);
                    recording = 0;
                    recv_index = 0;
                    recv_count = 0;
                    start_seq_count = 0;
                    stop_seq_count = 0;
                }
            }
        }
    }
    return 0;
}
