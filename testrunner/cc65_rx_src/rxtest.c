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

#define GRID_SIZE 10
#define SCREEN_WIDTH 40
#define SCREEN_HEIGHT 25

#define CHAR_BASE 0x0400
#define COLOR_BASE 0xD800

#define STATUS_LINE_Y 24

#define MAX_SEEN_CHARS 20

unsigned char seen_chars[MAX_SEEN_CHARS];
unsigned char seen_count = 0;

void draw_seen_chars(void) {
    unsigned char i;
    unsigned short offset;
    char hex_str[4];  // e.g. "$41\0"

    for (i = 0; i < seen_count; ++i) {
        offset = i * SCREEN_WIDTH + 0;  // column 0, row i
        // Format char as hex string with $ prefix
        hex_str[0] = '$';
        hex_str[1] = "0123456789ABCDEF"[(seen_chars[i] >> 4) & 0x0F];
        hex_str[2] = "0123456789ABCDEF"[seen_chars[i] & 0x0F];
        hex_str[3] = '\0';

        // Write the 3 chars horizontally
        *((unsigned char*)(CHAR_BASE + offset + 0)) = hex_str[0];
        *((unsigned char*)(COLOR_BASE + offset + 0)) = COLOR_YELLOW;
        *((unsigned char*)(CHAR_BASE + offset + 1)) = hex_str[1];
        *((unsigned char*)(COLOR_BASE + offset + 1)) = COLOR_YELLOW;
        *((unsigned char*)(CHAR_BASE + offset + 2)) = hex_str[2];
        *((unsigned char*)(COLOR_BASE + offset + 2)) = COLOR_YELLOW;

        // Clear any leftover char at col 3 for cleanliness
        *((unsigned char*)(CHAR_BASE + offset + 3)) = ' ';
        *((unsigned char*)(COLOR_BASE + offset + 3)) = COLOR_YELLOW;
    }

    // Clear lines below if fewer chars than MAX_SEEN_CHARS
    for (; i < MAX_SEEN_CHARS; ++i) {
        offset = i * SCREEN_WIDTH + 0;
        *((unsigned char*)(CHAR_BASE + offset + 0)) = ' ';
        *((unsigned char*)(COLOR_BASE + offset + 0)) = COLOR_YELLOW;
        *((unsigned char*)(CHAR_BASE + offset + 1)) = ' ';
        *((unsigned char*)(COLOR_BASE + offset + 1)) = COLOR_YELLOW;
        *((unsigned char*)(CHAR_BASE + offset + 2)) = ' ';
        *((unsigned char*)(COLOR_BASE + offset + 2)) = COLOR_YELLOW;
        *((unsigned char*)(CHAR_BASE + offset + 3)) = ' ';
        *((unsigned char*)(COLOR_BASE + offset + 3)) = COLOR_YELLOW;
    }
}



unsigned char colors[6] = {
    COLOR_WHITE, COLOR_RED, COLOR_YELLOW,
    COLOR_CYAN, COLOR_BLACK, COLOR_GREEN
};

char grid[GRID_SIZE][GRID_SIZE];
unsigned char grid_colors[GRID_SIZE][GRID_SIZE];

// Shift the grid content up by one row (scroll up)
void shift_grid_up(void) {
    unsigned char row, col;
    for (row = 0; row < GRID_SIZE - 1; ++row) {
        for (col = 0; col < GRID_SIZE; ++col) {
            grid[row][col] = grid[row + 1][col];
            grid_colors[row][col] = grid_colors[row + 1][col];
        }
    }
    // Clear the last row after shift
    for (col = 0; col < GRID_SIZE; ++col) {
        grid[GRID_SIZE - 1][col] = ' ';
        grid_colors[GRID_SIZE - 1][col] = COLOR_WHITE;
    }
}

// Draw the grid on screen using stored chars and colors
void draw_grid(void) {
    unsigned char row, col;
    unsigned char screen_row = (SCREEN_HEIGHT - GRID_SIZE) / 2;
    unsigned char screen_col = (SCREEN_WIDTH - GRID_SIZE) / 2;
    unsigned short screen_index;

    for (row = 0; row < GRID_SIZE; ++row) {
        for (col = 0; col < GRID_SIZE; ++col) {
            screen_index = (screen_row + row) * SCREEN_WIDTH + (screen_col + col);
            *((unsigned char*)(CHAR_BASE + screen_index)) = grid[row][col];
            *((unsigned char*)(COLOR_BASE + screen_index)) = grid_colors[row][col];
        }
    }
}

// Draw status line centered at line y
void draw_status_line(unsigned char y, const char* label, const char* msg, unsigned char text_color) {
    unsigned char i;
    unsigned short line_offset = y * SCREEN_WIDTH;
    unsigned char start_col = (SCREEN_WIDTH - 14) / 2;

    for (i = 0; i < SCREEN_WIDTH; ++i) {
        *((unsigned char*)(CHAR_BASE + line_offset + i)) = ' ';
        *((unsigned char*)(COLOR_BASE + line_offset + i)) = text_color;
    }

    for (i = 0; i < strlen(label); ++i) {
        *((unsigned char*)(CHAR_BASE + line_offset + start_col + i)) = label[i];
        *((unsigned char*)(COLOR_BASE + line_offset + start_col + i)) = text_color;
    }

    for (i = 0; i < strlen(msg); ++i) {
        *((unsigned char*)(CHAR_BASE + line_offset + start_col + strlen(label) + i)) = msg[i];
        *((unsigned char*)(COLOR_BASE + line_offset + start_col + strlen(label) + i)) = text_color;
    }
}


void draw_fixed_text(unsigned char y, unsigned char x, const char* text, unsigned char color) {
    unsigned short offset = y * SCREEN_WIDTH + x;
    unsigned char i;
    for (i = 0; text[i] != '\0'; i++) {
        *((unsigned char*)(CHAR_BASE + offset + i)) = text[i];
        *((unsigned char*)(COLOR_BASE + offset + i)) = color;
    }
}


// Initialize the 6551 ACIA for receive only
void init_acia(void) {
    ACIA_CMD = 0x0B;       // Enable TX/RX, RTS low (TX will be unused here)
    ACIA_CTRL = 0x0C;      // 9600 baud, 8N1, internal clock
}


int main(void) {
    unsigned char rx_ready, tx_ready;
    unsigned char rx_char;
    unsigned char col = 0;
    char char_info[20];
    char status_rx[10], status_tx[10];
    long i;

    clrscr();
    cputs("Swiftlink RX Grid Demo\n\r");
    init_acia();

    // Initialize grid with spaces and white color
    for (i = 0; i < GRID_SIZE * GRID_SIZE; ++i) {
        ((char*)grid)[i] = ' ';
        ((unsigned char*)grid_colors)[i] = COLOR_WHITE;
    }
    draw_grid();

    while (1) {
        rx_ready = (ACIA_STATUS & 0x08) ? 1 : 0;

        if (rx_ready) {
            rx_char = ACIA_DATA;  // Read received char

            sprintf(char_info, "Char: $%02X (%c)    ", rx_char, rx_char);
            draw_fixed_text(22, 0, char_info, COLOR_WHITE);

            if (rx_char == 0xA3 || rx_char == 0x5C) {
                continue;
            }

            // Check if rx_char already in seen_chars
            {
                unsigned char found = 0;
                unsigned char k;
                for (k = 0; k < seen_count; ++k) {
                    if (seen_chars[k] == rx_char) {
                        found = 1;
                        break;
                    }
                }

                if (!found) {
                    if (seen_count < MAX_SEEN_CHARS) {
                        seen_chars[seen_count++] = rx_char;
                    } else {
                        // Scroll buffer up and add new char at end
                        for (k = 1; k < MAX_SEEN_CHARS; ++k) {
                            seen_chars[k - 1] = seen_chars[k];
                        }
                        seen_chars[MAX_SEEN_CHARS - 1] = rx_char;
                    }
                    draw_seen_chars();
                }
            }

            // Store char in grid and assign random color
            grid[GRID_SIZE - 1][col] = rx_char;
            grid_colors[GRID_SIZE - 1][col] = colors[rand() % 6];

            col++;

            for (i = 0; i < 500; ++i);  // Fake delay

            if (col >= GRID_SIZE) {
                col = 0;
                shift_grid_up();
            }

            draw_grid();

            tx_ready = 1;  // TX not used but mark ready
            strcpy(status_rx, rx_ready ? "Full " : "Empty");
            strcpy(status_tx, tx_ready ? "Ready" : "Busy ");
            draw_status_line(23, "RX: ", status_rx, rx_ready ? COLOR_RED : COLOR_GREEN);
            draw_status_line(24, "TX: ", status_tx, tx_ready ? COLOR_GREEN : COLOR_RED);
        }
    }

    return 0;
}
