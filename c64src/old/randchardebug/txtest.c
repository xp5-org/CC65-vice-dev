#include <conio.h>
#include <peekpoke.h>
#include <stdlib.h>
#include <string.h>
#include <c64.h>
#include <cbm_petscii_charmap.h>

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

unsigned char colors[6] = {
    COLOR_WHITE, COLOR_RED, COLOR_YELLOW,
    COLOR_CYAN, COLOR_BLACK, COLOR_GREEN
};

char grid[GRID_SIZE][GRID_SIZE];
unsigned char grid_colors[GRID_SIZE][GRID_SIZE];

unsigned char get_color_for_char(unsigned char ch) {
    return colors[ch % 6];
}

void compose_status(char* buf, unsigned char rx_status, unsigned char tx_status) {
    strcpy(buf, "RX: ");
    strcat(buf, rx_status ? "Full  " : "Empty ");
    strcat(buf, "TX: ");
    strcat(buf, tx_status ? "Ready" : "Busy ");
}

void wait_tx_ready(void) {
    unsigned int timeout = 0xFFFF;
    while (!(ACIA_STATUS & 0x02) && timeout--) {
    }
}

void init_acia(void) {
    ACIA_CMD = 0x0B;
    ACIA_CTRL = 0x0C;
}

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

int main(void) {
    unsigned char rx_ready, tx_ready;
    char status_rx[10], status_tx[10];
    long i;
    unsigned char grid_row = 0;
    unsigned char grid_col = 0;

    clrscr();
    cputs("Swiftlink TX Demo\n\r");
    init_acia();

    memset(grid, ' ', sizeof(grid));

    while (1) {
        unsigned char ch = 'A' + (rand() % 26);
        unsigned char color = get_color_for_char(ch);

        gotoxy(0, STATUS_LINE_Y - 2);
        cprintf("Sending: %c   ", ch);

        tx_ready = 0;
        rx_ready = (ACIA_STATUS & 0x08) ? 1 : 0;

        strcpy(status_rx, rx_ready ? "Full " : "Empty");
        strcpy(status_tx, tx_ready ? "Ready" : "Busy ");
        draw_status_line(23, "RX: ", status_rx, rx_ready ? COLOR_RED : COLOR_GREEN);
        draw_status_line(24, "TX: ", status_tx, tx_ready ? COLOR_GREEN : COLOR_RED);

        ACIA_DATA = ch;
        for (i = 0; i < 3000; ++i);  // delay

        grid[grid_row][grid_col] = ch;
        grid_colors[grid_row][grid_col] = color;

        {
            unsigned char screen_row = (SCREEN_HEIGHT - GRID_SIZE) / 2 + grid_row;
            unsigned char screen_col = (SCREEN_WIDTH - GRID_SIZE) / 2 + grid_col;
            unsigned short screen_index = screen_row * SCREEN_WIDTH + screen_col;
            *((unsigned char*)(CHAR_BASE + screen_index)) = ch;
            *((unsigned char*)(COLOR_BASE + screen_index)) = color;
        }

        grid_col++;
        if (grid_col >= GRID_SIZE) {
            grid_col = 0;
            grid_row++;
            if (grid_row >= GRID_SIZE) {
                grid_row = 0;
                memset(grid, ' ', sizeof(grid));
                memset(grid_colors, COLOR_WHITE, sizeof(grid_colors));
                draw_grid();
            }
        }
    }

    return 0;
}
