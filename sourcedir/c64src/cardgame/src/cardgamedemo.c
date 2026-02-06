#include <stdio.h>
#include <conio.h>
#include <string.h>
#include <stdio.h>
#include <conio.h>
#include <tgi.h>
#include <conio.h>
#include "common.h"
#include <stdio.h>
#include <cbm_petscii_charmap.h>




const char SPRITE_DATA[64] = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x18, 0x00, 0x00, 0x3C, 0x00, 0x00,
    0x7E, 0x00, 0x00, 0xFF, 0x00, 0x01, 0xFF, 0x80,
    0x03, 0xFF, 0xC0, 0x07, 0xFF, 0xE0, 0x0F, 0xFF,
    0xF0, 0x1F, 0xFF, 0xF8, 0x00, 0xFF, 0x00, 0x00,
    0xFF, 0x00, 0x00, 0xFF, 0x00, 0x00, 0xFF, 0x00,
    0x00, 0xFF, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};



// set the background color
void setScreenColor(char color) {
    *((char*)0xD021) = color;
}

// clear the screen with spaces and set background color
void clearScreen(char bgColor) {
    int i; 
    
    // Fill the screen with spaces (character code 32)
    for (i = 0; i < 1000; ++i) {
        *((char*)0x0400 + i) = 32;
        *((char*)0xD800 + i) = bgColor; // Set color RAM to the background color
    }
}


void convertToPETSCII(char* text) {
    int i;
    char character;

    for (i = 0; text[i] != '\0'; ++i) {
        character = text[i];

        // convert ASCII characters to PETSCII codes
        if (character >= 65 && character <= 90) {
            // handle uppercase letters
            text[i] = character + 128;
        } else if (character >= 97 && character <= 122) {
            // handle lowercase letters
            text[i] = character - 32;
        } else {
            // other characters unchanged
        }
    }
}


#define GRID_ROWS 8
#define GRID_COLS 8
#define CARD_WIDTH 3
#define CARD_HEIGHT 4
#define CARD_SPACING 1 // Spacing between each card
#define CARD_VERT_SPACING 2

/* Standardized structure */
typedef struct {
    int value;
    int cardType;
    int touched;
    int x, y;          /* Character positions (0-39, 0-24) */
    int x1, x2, y1, y2; /* Pixel boundaries for sprite collision */
} Card;

Card grid[GRID_ROWS][GRID_COLS];

void initializeScreen() {
    int xx, yy;
    int base_x = 5;
    int base_y = 5;

    for (yy = 0; yy < GRID_ROWS; ++yy) {
        for (xx = 0; xx < GRID_COLS; ++xx) {
            grid[yy][xx].x = base_x + (xx * (CARD_WIDTH + CARD_SPACING));
            grid[yy][xx].y = base_y + (yy * CARD_VERT_SPACING);
            
            /* Calculate pixel boundaries: (Char * 8) + HardwareBorderOffset */
            grid[yy][xx].x1 = 24 + (grid[yy][xx].x * 8); 
            grid[yy][xx].x2 = grid[yy][xx].x1 + (CARD_WIDTH * 8);
            grid[yy][xx].y1 = 50 + (grid[yy][xx].y * 8);
            grid[yy][xx].y2 = grid[yy][xx].y1 + (CARD_HEIGHT * 8);
        }
    }
}

int findCardAtPixels(int px, int py, int *row, int *col) {
    int r, c;
    /* Use the center of the 24x21 sprite as the 'click' point */
    int mx = px + 12; 
    int my = py + 10;

    for (r = 0; r < GRID_ROWS; ++r) {
        for (c = 0; c < GRID_COLS; ++c) {
            if (mx >= grid[r][c].x1 && mx <= grid[r][c].x2 &&
                my >= grid[r][c].y1 && my <= grid[r][c].y2) {
                *row = r;
                *col = c;
                return 1;
            }
        }
    }
    return 0;
}




void setCard(int row, int col, int cardValue, int cardType) {
    Card *card; // Declare pointer to Card

    // Assign pointer to specific card in grid
    card = &grid[row][col];

    // Set card value and type
    card->value = cardValue;
    card->cardType = cardType;
}



 

void drawRectangle(int x, int y, int width, int height, int value) {
    int i, j; 
    int screenPos; // Declare screenPos at the beginning
    
    // Check if value is 0 and return early if true
    if (value == 0) {
        return;
    }

    // Iterate through the rectangle area
    for (i = 0; i < height; ++i) {
        for (j = 0; j < width; ++j) {
            // Calculate the screen memory location
            screenPos = (y + i) * 40 + x + j;
            *((char*)0x0400 + screenPos) = 160; // Set character code for white rectangle
            *((char*)0xD800 + screenPos) = 1;   // Set color RAM to white
            
            // Check for upper left corner to draw number 1
            if (i == 0 && j == 0) {
                *((char*)0x0400 + screenPos) = value; // Place first character of value in upper left corner
            }
            
            // Check for lower right corner to draw number 2
            if (i == height - 1 && j == width - 1) {
                *((char*)0x0400 + screenPos) = value; // Place last character of value in lower right corner
            }
        }
    }
}

void clear_screen(unsigned char fill_char) {
    unsigned char* screen;
    int i;

    screen = (unsigned char*)0x0400; // Starting address of the screen memory
    for (i = 0; i < 1000; ++i) { // 25 rows * 40 columns = 1000 character cells
        screen[i] = fill_char;
    }
}




void putText(int x, int y, const char* text, char color) {
    int len = strlen(text);
    int i;

    // Calculate the base address for the start position
    char* textBase = (char*)0x0400 + y * 40 + x;
    char* colorBase = (char*)0xD800 + y * 40 + x;

    // Clear the top of screen text area before writing
    //for (i = 0; i < 40; ++i) {
    //    *((char*)0x0400 + i) =  2; // Clear previous text with spaces
    //    *((char*)0xD800 + i) = color; // Set color RAM to specified color
    //}

    // Write the text at the specified position
    for (i = 0; i < len; ++i) {
        *(textBase + i) = text[i]; // Write the text
        *(colorBase + i) = color;  // Set color RAM to specified color
    }
}

void pixelToRowCol(int pixelX, int pixelY, int *row, int *col) {
    // adjust pixel coordinates by startX and startY offsets
    int adjustedX = pixelX - (5 * 8) - 12;  // Adjust for startX
    int adjustedY = pixelY - (5 * 8) - 48;  // Adjust for startY
    // take away for sprite height?
  
    // calculate column index
    *col = adjustedX / (CARD_WIDTH * 8 + CARD_SPACING * 8);

    // calculate row index
    // each card is 2 rows tall, and each row is 8 pixels high
    *row = adjustedY / (CARD_VERT_SPACING * 8 );
}


unsigned char read_raster_line() {
    return *((unsigned char*)0xD012);
}


int main() {
   // int i; // Declarations moved to the beginning of the block
  char output[34];
    // variables
  int x = 172;	// sprite X position (16-bit)
  byte y = 145; // sprite Y position (8-bit)
  byte bgcoll;	// sprite background collision flags
  byte joy;	// joystick flags
  int ix, iy;
  int row, col;
  int random_number;

  
  // begin card grid stuff
    int xx, yy; // Loop counters

    // initialize screen and get startX and startY
    initializeScreen();
    srand(read_raster_line());
    srand(8765432);

  // init card matrix with random values 1-26
    for (iy = 0; iy < GRID_ROWS; ++iy) {
        for (ix = 0; ix < GRID_COLS; ++ix) {
          random_number = rand() % 26 + 1;
            setCard(ix, iy, random_number, 1); // Set each card to have value 27 and card type 1
          //printf("%d\n", random_number);
        }
    }
  
    // Set some example cards, card type 0 is blankcard
    // int row, int col, int cardValue, int cardType
    //setCard(0, 0, 0, 1);   // Regular card number 1
    //setCard(0, 1, 0, 15); // Special card number 10
    //setCard(0, 2, 0, 15);   // Regular card number 1
    //setCard(0, 3, 0, 15);   // Regular card number 1
  
  
  
  // copy sprite pattern to RAM address 0x3800
  memcpy((char*)0x3800, SPRITE_DATA, sizeof(SPRITE_DATA));
  // set sprite #0 shape entry (224)
  POKE(0x400 + 0x3f8 + 0, 0x3800 / 64);
  // set position and color
  VIC.spr_pos[0].x = 172;
  VIC.spr_pos[0].y = 145;
  VIC.spr_color[0] = COLOR_GREEN;
  // enable sprite #0
  VIC.spr_ena = 0b00000001;
  
  // install the joystick driver
  joy_install (joy_static_stddrv);
    clearScreen(0);
  
  

    // set black background color
    setScreenColor(2);
  
  
  // Iterate over rows & cols and draw a card/rectangle for each entry
      for (yy = 0; yy < GRID_ROWS; ++yy) {
        for (xx = 0; xx < GRID_COLS; ++xx) {
          drawRectangle(grid[yy][xx].x, grid[yy][xx].y, 3, 4, grid[yy][xx].value);
           // printf("C[%d][%d]: X = %d, Y = %d, ID = %d, Type = %d\n",
           //        yy, xx, grid[yy][xx].x, grid[yy][xx].y, grid[yy][xx].value, grid[yy][xx].cardType);
         // printf("%d", grid[yy][xx].value);
        }
    }
   

    while (1) { // Infinite loop
          // get joystick bits
    joy = joy_read(0);
    // move sprite based on joystick
    if (JOY_LEFT(joy)) { x -= 2; }   // move left 1 pixel
    if (JOY_RIGHT(joy)) { x += 2; }  // move right 1 pixel
    if (JOY_UP(joy)) { y -= 2; }     // move up 1 pixel
    if (JOY_DOWN(joy)) { y += 2; }   // move down 1 pixel
    // wait for end of frame
    waitvsync();
    // set sprite registers based on position
    VIC.spr_pos[0].x = x;
    VIC.spr_pos[0].y = y;
if (JOY_FIRE(joy)) {
        if (findCardAtPixels(x, y, &row, &col)) {
            snprintf(output, sizeof(output), "RC: %02d %02d VAL: %02d", row, col, grid[row][col].value);
            putText(1, 24, output, 3);
        } else {
            putText(1, 24, "NO CARD SELECTED          ", 3);
        }
    }

    // set X coordinate high bit
    VIC.spr_hi_x = (x & 0x100) ? 1 : 0;
    // grab and reset collision flags
    bgcoll = VIC.spr_bg_coll;
    // change color when we collide with background
    VIC.spr_color[0] = (bgcoll & 1) ?
      COLOR_YELLOW : COLOR_GREEN;
    }
    return 0;
}