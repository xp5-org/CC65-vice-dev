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
    ACIA_CMD = 0x0B;       // TX/RX enable, RTS low
    ACIA_CTRL = 0x0C;      // 9600 baud, internal clock
}


void fill_grid_random(void) {
    unsigned char row, col;
    for (row = 0; row < GRID_SIZE; ++row) {
        for (col = 0; col < GRID_SIZE; ++col) {
            grid[row][col] = 'A' + (rand() % 26);
            grid_colors[row][col] = colors[rand() % 6];
        }
    }
}


void shift_grid_up(void) {
    unsigned char row, col;
    for (row = 0; row < GRID_SIZE - 1; ++row) {
        for (col = 0; col < GRID_SIZE; ++col) {
            grid[row][col] = grid[row + 1][col];
            grid_colors[row][col] = grid_colors[row + 1][col];
        }
    }
    for (col = 0; col < GRID_SIZE; ++col) {
        grid[GRID_SIZE - 1][col] = 'A' + (rand() % 26);
        grid_colors[GRID_SIZE - 1][col] = colors[rand() % 6];
    }
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
    unsigned char col;
    unsigned char rx_ready, tx_ready;
    char status_rx[10], status_tx[10];
   long i;

    clrscr();
    cputs("Swiftlink TX Grid Demo\n\r");
    init_acia();
    fill_grid_random();
    draw_grid();

    while (1) {
        for (col = 0; col < GRID_SIZE; ++col) {
            unsigned char ch = grid[0][col];

            gotoxy(0, STATUS_LINE_Y - 2);
            cprintf("Sending: %c   ", ch);

            tx_ready = 0;
            rx_ready = (ACIA_STATUS & 0x08) ? 1 : 0;

            strcpy(status_rx, rx_ready ? "Full " : "Empty");
            strcpy(status_tx, tx_ready ? "Ready" : "Busy ");
            draw_status_line(23, "RX: ", status_rx, rx_ready ? COLOR_RED : COLOR_GREEN);
            draw_status_line(24, "TX: ", status_tx, tx_ready ? COLOR_GREEN : COLOR_RED);

            ACIA_DATA = ch;
            //wait_tx_ready();
          //ACIA_DATA = ch;
		for (i = 0; i < 3000; ++i);  // Fake delay


            tx_ready = 1;
            rx_ready = (ACIA_STATUS & 0x08) ? 1 : 0;

            strcpy(status_rx, rx_ready ? "Full " : "Empty");
            strcpy(status_tx, tx_ready ? "Ready" : "Busy ");
            draw_status_line(23, "RX: ", status_rx, rx_ready ? COLOR_RED : COLOR_GREEN);
            draw_status_line(24, "TX: ", status_tx, tx_ready ? COLOR_GREEN : COLOR_RED);

           // while (1) {
           //     volatile unsigned char dummy = ACIA_DATA;
           //     (void)dummy;
           // }
        }

        shift_grid_up();
        draw_grid();
    }

    return 0;
}
