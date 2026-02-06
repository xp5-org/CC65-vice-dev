#include <stdio.h>
#include <conio.h>
#include <tgi.h>

# define font1_width = 4;
# define font2_width = 7;

extern void cycle_counter(void);

const unsigned short alphabet[40][4] = {
    {0b1111, 0b1001, 0b1111, 0b1001}, // A
    {0b1000, 0b1110, 0b1010, 0b1110}, // B
    {0b1111, 0b1000, 0b1000, 0b1111}, // C
    {0b1110, 0b1001, 0b1001, 0b1110}, // D
    {0b1111, 0b1110, 0b1000, 0b1111}, // E
    {0b1111, 0b1110, 0b1000, 0b1000}, // F
    {0b1111, 0b1000, 0b1001, 0b1111}, // G
    {0b1000, 0b1000, 0b1111, 0b1001}, // H
    {0b0100, 0b0100, 0b0100, 0b0100}, // I
    {0b0100, 0b0100, 0b0100, 0b1100}, // J
    {0b1010, 0b1100, 0b1010, 0b1001}, // K
    {0b1000, 0b1000, 0b1000, 0b1111}, // L
    {0b1001, 0b1111, 0b1001, 0b1001}, // M
    {0b1001, 0b1101, 0b1011, 0b1001}, // N
    {0b1111, 0b1001, 0b1001, 0b1111}, // O
    {0b1111, 0b1001, 0b1110, 0b1000}, // P
    {0b1111, 0b1001, 0b1111, 0b0001}, // Q
    {0b1110, 0b1001, 0b1100, 0b1010}, // R
    {0b1111, 0b1000, 0b0001, 0b1111}, // S
    {0b1111, 0b0100, 0b0100, 0b0100}, // T
    {0b1001, 0b1001, 0b1001, 0b1111}, // U
    {0b1001, 0b0101, 0b0011, 0b0001}, // V
    {0b1001, 0b1001, 0b1001, 0b0110}, // W
    {0b0000, 0b1010, 0b0100, 0b1010}, // X
    {0b1001, 0b0110, 0b0010, 0b0010}, // Y
    {0b1111, 0b0100, 0b0010, 0b1111}, // Z
    {0b0110, 0b1010, 0b1010, 0b1100}, // 0
    {0b0010, 0b0110, 0b0010, 0b0010}, // 1
    {0b0110, 0b0010, 0b0100, 0b0110}, // 2
    {0b0110, 0b0011, 0b0001, 0b0110}, // 3
    {0b0101, 0b0111, 0b0001, 0b0001}, // 4
    {0b0110, 0b0100, 0b0010, 0b0110}, // 5
    {0b0100, 0b0110, 0b0101, 0b0011}, // 6
    {0b0111, 0b0101, 0b0001, 0b0001}, // 7
    {0b0111, 0b0101, 0b0111, 0b0111}, // 8
    {0b0110, 0b0101, 0b0011, 0b0001}, // 9
    {0b0000, 0b0000, 0b0100, 0b1000}, // , comma
    {0b0000, 0b0000, 0b0110, 0b0110}, // . decimal
    {0b0001, 0b0010, 0b0100, 0b1000}, // /forwardslash
      {0b0001, 0b0010, 0b0100, 0b1000}, // /forwardslash
};


const unsigned short cryllic7x7[33][7] = {
{0b0000000,0b0011000,0b0100100,0b0100100,0b0111100,0b0100100,0b0000000}, // А
{0b0000000,0b0111100,0b0100000,0b0111000,0b0100100,0b0111000,0b0000000}, // Б
{0b0000000,0b0111000,0b0100100,0b0111000,0b0100100,0b0111000,0b0000000}, // В
{0b0000000,0b0111100,0b0100000,0b0100000,0b0100000,0b0100000,0b0000000}, // Г
{0b0000000,0b0001100,0b0010100,0b0010100,0b0111110,0b0100010,0b0000000}, // Д
{0b0000000,0b0111100,0b0100000,0b0111000,0b0100000,0b0111100,0b0000000}, // Е
{0b0000000,0b0101010,0b0101010,0b0011100,0b0101010,0b0101010,0b0000000}, // Ж
{0b0000000,0b0011000,0b0000100,0b0011000,0b0000100,0b0011000,0b0000000}, // З
{0b0000000,0b0100010,0b0100110,0b0101010,0b0110010,0b0100010,0b0000000}, // И
{0b0010100,0b0001000,0b0100010,0b0100110,0b0101010,0b0110010,0b0000000}, // Й
{0b0000000,0b0100100,0b0101000,0b0110000,0b0101000,0b0100100,0b0000000}, // К
{0b0000000,0b0001100,0b0010100,0b0010100,0b0010100,0b0100100,0b0000000}, // Л
{0b0000000,0b0100010,0b0110110,0b0101010,0b0100010,0b0100010,0b0000000}, // М
{0b0000000,0b0100100,0b0100100,0b0111100,0b0100100,0b0100100,0b0000000}, // Н
{0b0000000,0b0011000,0b0100100,0b0100100,0b0100100,0b0011000,0b0000000}, // О
{0b0000000,0b0111100,0b0100100,0b0100100,0b0100100,0b0100100,0b0000000}, // П
{0b0000000,0b0111000,0b0100100,0b0100100,0b0111000,0b0100000,0b0000000}, // Р
{0b0000000,0b0011100,0b0100000,0b0100000,0b0100000,0b0011100,0b0000000}, // С
{0b0000000,0b0111110,0b0001000,0b0001000,0b0001000,0b0001000,0b0000000}, // Т
{0b0000000,0b0100100,0b0100100,0b0011100,0b0000100,0b0111000,0b0000000}, // У
{0b0000000,0b0011100,0b0101010,0b0101010,0b0011100,0b0001000,0b0000000}, // Ф
{0b0000000,0b0100010,0b0010100,0b0001000,0b0010100,0b0100010,0b0000000}, // Х
{0b0000000,0b0100100,0b0100100,0b0100100,0b0100100,0b0111110,0b0000010}, // Ц
{0b0000000,0b0100100,0b0100100,0b0011100,0b0000100,0b0000100,0b0000000}, // Ч
{0b0000000,0b0101010,0b0101010,0b0101010,0b0101010,0b0111110,0b0000000}, // Ш
{0b0000000,0b0101010,0b0101010,0b0101010,0b0101010,0b0111111,0b0000001}, // Щ
{0b0000000,0b0110000,0b0010000,0b0011100,0b0010010,0b0011100,0b0000000}, // Ъ
{0b0000000,0b1000010,0b1000010,0b1110010,0b1001010,0b1110010,0b0000000}, // Ы
{0b0000000,0b0100000,0b0100000,0b0111000,0b0100100,0b0111000,0b0000000}, // Ь
{0b0000000,0b0111000,0b0000100,0b0011100,0b0000100,0b0111000,0b0000000}, // Э
{0b0000000,0b1001100,0b1010010,0b1110010,0b1010010,0b1001100,0b0000000}, // Ю
{0b0000000,0b0011100,0b0100100,0b0011100,0b0100100,0b0100100,0b0000000}, // Я
{0b0010100,0b0111100,0b0100000,0b0111000,0b0100000,0b0111100,0b0000000} // Ё
};




int findcharindex(char character) {
    // only supports uppercase A-Z, digits 0-9, comma, period, and forward slash
    if (character >= 'A' && character <= 'Z') {
        return character - 'A';
    } else if (character >= '0' && character <= '9') {
        return character - '0' + 26;
    } else if (character == ',') {
        return 36; // Index for comma
    } else if (character == '.') {
        return 37; // Index for period
    } else if (character == '/') {
        return 38; // Index for forward slash
    } else {
        return -1; // Not found in the array
    }
}








#include <stdio.h>
#include <string.h>

/* Lookup table for ASCII to Font Index mapping */
static unsigned char char_map[256];

void init_char_map() {
    unsigned char i;
    /* Faster than a loop for 6502 */
    memset(char_map, 255, 256);

    for (i = 0; i < 26; ++i) char_map['A' + i] = i;
    for (i = 0; i < 10; ++i) char_map['0' + i] = i + 26;
    
    char_map[','] = 36;
    char_map['.'] = 37;
    char_map['/'] = 38;
}


void drawchar(char fontnumber, char character, unsigned int startX, unsigned char startY) {
    unsigned char y;
    unsigned char index;
    const unsigned short* row_ptr;
    unsigned char row_bits;
    
    index = char_map[(unsigned char)character];
    if (index == 255) return;

    if (fontnumber == 1) {
        row_ptr = alphabet[index];
        for (y = 0; y < 4; ++y) {
            row_bits = (unsigned char)row_ptr[y];
            /* shift 4 times because it's a 4px font */
            if (row_bits & 0x08) tgi_setpixel(startX,     startY + y);
            if (row_bits & 0x04) tgi_setpixel(startX + 1, startY + y);
            if (row_bits & 0x02) tgi_setpixel(startX + 2, startY + y);
            if (row_bits & 0x01) tgi_setpixel(startX + 3, startY + y);
        }
    } else {
        row_ptr = cryllic7x7[index];
        for (y = 0; y < 7; ++y) {
            row_bits = (unsigned char)row_ptr[y];
            /* Unrolled loop for 7px wide font */
            if (row_bits & 0x40) tgi_setpixel(startX,     startY + y);
            if (row_bits & 0x20) tgi_setpixel(startX + 1, startY + y);
            if (row_bits & 0x10) tgi_setpixel(startX + 2, startY + y);
            if (row_bits & 0x08) tgi_setpixel(startX + 3, startY + y);
            if (row_bits & 0x04) tgi_setpixel(startX + 4, startY + y);
            if (row_bits & 0x02) tgi_setpixel(startX + 5, startY + y);
            if (row_bits & 0x01) tgi_setpixel(startX + 6, startY + y);
        }
    }
}




// limited to 8px font due to bit shift calc? 
void drawstring(char fontnumber, const char* str, unsigned int startX, unsigned char startY) {
    //* Font 1: 4px wide + 1px gap = 5 */
    int spacing = (fontnumber == 1) ? 5 : 6; 
    while (*str) {
        drawchar(fontnumber, *str, startX, startY);
        startX += spacing;
        str++;
    }
}

// limited to 8px font due to bit shift calc? 
void drawWrappedString(char fontnumber, const char* text, unsigned char maxLineLength, unsigned char startX, unsigned char startY) {
    int char_w = (fontnumber == 1) ? 5 : 6;
    int space_w = (fontnumber == 1) ? 3 : 3;
    int line_h = (fontnumber == 1) ? 5 : 6;
    unsigned int curX = startX;
    unsigned int curY = startY;
    const char* ptr = text;
    char word[32];
    int word_idx = 0;

    while (1) {
        if (*ptr == ' ' || *ptr == '\0') {
            word[word_idx] = '\0';
            if (word_idx > 0) {
                /* Check if word fits: (letters * width) */
                if (curX + (word_idx * char_w) > startX + (maxLineLength * char_w)) {
                    curX = startX;
                    curY += line_h;
                }
                
                drawstring(fontnumber, word, curX, curY);
                curX += (word_idx * char_w) + space_w;
            } else if (*ptr == ' ') {
                curX += space_w;
            }

            word_idx = 0;
            if (*ptr == '\0') break;
        } else {
            if (word_idx < 31) {
                word[word_idx++] = *ptr;
            }
        }
        ptr++;
    }
}



void someDelay() {
    int delayCount = 30000; 
    while (delayCount > 0) {
        asm("nop");
        delayCount--;
    }
}


int main() {
    int i, linespacing;
    int kbhit_check;
   const char* myLongString1 = "NOW IS A TIME FOR ALL GOOD MEN TO COME TO THE AID OF THEIR COUNTRY. IN THIS MOMENT, WHERE THE FUTURE UNFOLDS BEFORE US, EACH INDIVIDUAL HOLDS THE POWER TO SHAPE THE DESTINY OF OUR NATION. LET US RISE TO THE CHALLENGES THAT CONFRONT US, UNITED IN OUR DIVERSITY, STRIVING FOR A COMMON PURPOSE. NOW IS NOT THE MOMENT FOR APATHY, BUT FOR ACTIVE ENGAGEMENT IN BUILDING A SOCIETY ROOTED IN JUSTICE, EQUALITY, AND FREEDOM. TOGETHER, WE CAN OVERCOME ADVERSITY, FOSTER UNITY, AND SECURE A BETTER TOMORROW. NOW, MORE THAN EVER, IS THE TIME FOR ALL GOOD MEN AND WOMEN TO STAND TOGETHER, EMBRACING THE RESPONSIBILITY THAT HISTORY BESTOWS UPON US, FOR IN OUR COLLECTIVE ACTIONS LIES THE STRENGTH OF OUR NATION";
 const char* myLongString2 = "WITH GREAT POWER COMES GREAT RESPONSIBILITY. THIS ADMONITION, ATTRIBUTED TO VARIOUS FIGURES THROUGH HISTORY, ENCOURAGES INDIVIDUALS TO RECOGNIZE THE IMPACT OF THEIR ACTIONS AND TO USE THEIR INFLUENCE WISELY. IT REMINDS US THAT POSSESSING ABILITIES, BE THEY INTELLECTUAL, SOCIAL, OR OTHERWISE, BRINGS A DUTY TO CONTRIBUTE TO THE GREATER GOOD OF SOCIETY. IN THE FACE OF OPPORTUNITY, LET US STRIVE TO UPLIFT AND EMPOWER THOSE AROUND US, FOSTERING A COMMUNITY BUILT ON MUTUAL RESPECT AND KINDNESS.";
  const char* myLongString3 = "BE THE CHANGE YOU WISH TO SEE IN THE WORLD. THIS INSPIRING UTTERANCE, OFTEN ATTRIBUTED TO MAHATMA GANDHI, ENCOURAGES INDIVIDUALS TO TAKE INITIATIVE IN CREATING POSITIVE TRANSFORMATIONS. IT CALLS FOR SELF-AWARENESS, PROMPTING US TO REFLECT ON OUR VALUES AND ASPIRATIONS";
  const char* mystring1 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789,./"; 
  const char* mystring2 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123";
    // Install TGI
    tgi_install(tgi_static_stddrv); 
    tgi_init(); // init tgi
    tgi_clear(); // Clear the screen
init_char_map();
    // Check if tgi_init() failed
    if (tgi_geterror() != TGI_ERR_OK) {
        printf("Error initializing graphics.");
        return 1;
    }
  

drawWrappedString(1, myLongString1, 63, 2, 1); // character array, string, maxLineLength, startX, startY, scalefactor
drawWrappedString(1, myLongString2, 32, 2, 84); // character array, string, maxLineLength, startX, startY, scalefactor
drawWrappedString(2, myLongString3, 22, 178, 84); // character array, string, maxLineLength, startX, startY, scalefactor



  
  
  
  

  tgi_clear();
    do {  // DEMO text wall
       for (i = 0; i < 180; i+=15){
         linespacing = 18;
         drawstring(1, mystring1, 2, i); // character array, string, startX, startY
          drawstring(2, mystring2, 2, i + 5); // character array, string, startX, startY
          
        }
    someDelay();
          

           
    //reset
    tgi_clear();
      
    kbhit_check = kbhit(); 
    } while (!kbhit_check); // Wait for a key press before exiting

  
    tgi_done(); // Clean up TGI
    return 0;
}