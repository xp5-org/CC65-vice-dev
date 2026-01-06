#include <stdio.h>
#include <cc65.h>
#include <modload.h>
#include <tgi.h> 
#include <conio.h>  // Needed for text output to the C64 screen
#include <string.h>


static const int sine[] = {
    0, 174, 348, 523, 697, 871, 1045, 1218, 1391, 1564, 1736, 1908, 2079, 2249, 2419, 2588, 
    2756, 2923, 3090, 3255, 3420, 3583, 3746, 3907, 4067, 4226, 4384, 4540, 4695, 4848, 5000, 5150, 
    5299, 5446, 5592, 5736, 5878, 6018, 6157, 6293, 6428, 6561, 6691, 6820, 6947, 7071, 7193, 7314, 
    7431, 7547, 7660, 7771, 7880, 7986, 8090, 8192, 8290, 8387, 8480, 8572, 8660, 8746, 8829, 8910, 
    8988, 9063, 9135, 9205, 9272, 9336, 9397, 9455, 9511, 9563, 9613, 9659, 9703, 9744, 9781, 9816, 
    9848, 9877, 9903, 9925, 9945, 9961, 9975, 9986, 9994, 9998, 10000, 9998, 9994, 9986, 9975, 9961, 
    9945, 9925, 9903, 9877, 9848, 9816, 9781, 9744, 9703, 9659, 9613, 9563, 9511, 9455, 9397, 9336, 
    9272, 9205, 9135, 9063, 8988, 8910, 8829, 8746, 8660, 8572, 8480, 8387, 8290, 8192, 8090, 7986, 
    7880, 7771, 7660, 7547, 7431, 7314, 7193, 7071, 6947, 6820, 6691, 6561, 6428, 6293, 6157, 6018, 
    5878, 5736, 5592, 5446, 5299, 5150, 5000, 4848, 4695, 4540, 4384, 4226, 4067, 3907, 3746, 3583, 
    3420, 3255, 3090, 2923, 2756, 2588, 2419, 2249, 2079, 1908, 1736, 1564, 1391, 1218, 1045, 871, 
    697, 523, 348, 174, 0, -174, -348, -523, -697, -871, -1045, -1218, -1391, -1564, -1736, -1908, 
    -2079, -2249, -2419, -2588, -2756, -2923, -3090, -3255, -3420, -3583, -3746, -3907, -4067, -4226, 
    -4384, -4540, -4695, -4848, -5000, -5150, -5299, -5446, -5592, -5736, -5878, -6018, -6157, -6293, 
    -6428, -6561, -6691, -6820, -6947, -7071, -7193, -7314, -7431, -7547, -7660, -7771, -7880, -7986, 
    -8090, -8192, -8290, -8387, -8480, -8572, -8660, -8746, -8829, -8910, -8988, -9063, -9135, -9205, 
    -9272, -9336, -9397, -9455, -9511, -9563, -9613, -9659, -9703, -9744, -9781, -9816, -9848, -9877, 
    -9903, -9925, -9945, -9961, -9975, -9986, -9994, -9998, -10000, -9998, -9994, -9986, -9975, -9961, 
    -9945, -9925, -9903, -9877, -9848, -9816, -9781, -9744, -9703, -9659, -9613, -9563, -9511, -9455, 
    -9397, -9336, -9272, -9205, -9135, -9063, -8988, -8910, -8829, -8746, -8660, -8572, -8480, -8387, 
    -8290, -8192, -8090, -7986, -7880, -7771, -7660, -7547, -7431, -7314, -7193, -7071, -6947, -6820, 
    -6691, -6561, -6428, -6293, -6157, -6018, -5878, -5736, -5592, -5446, -5299, -5150, -5000, -4848, 
    -4695, -4540, -4384, -4226, -4067, -3907, -3746, -3583, -3420, -3255, -3090, -2923, -2756, -2588, 
    -2419, -2249, -2079, -1908, -1736, -1564, -1391, -1218, -1045, -871, -697, -523, -348, -174
};


static const int cosine[] = {
    10000, 9998, 9994, 9986, 9975, 9961, 9945, 9925, 9903, 9877, 9848, 9816, 9781, 9744, 9703, 9659, 
    9613, 9563, 9511, 9455, 9397, 9336, 9272, 9205, 9135, 9063, 8988, 8910, 8829, 8746, 8660, 8572, 
    8480, 8387, 8290, 8192, 8090, 7986, 7880, 7771, 7660, 7547, 7431, 7314, 7193, 7071, 6947, 6820, 
    6691, 6561, 6428, 6293, 6157, 6018, 5878, 5736, 5592, 5446, 5299, 5150, 5000, 4848, 4695, 4540, 
    4384, 4226, 4067, 3907, 3746, 3583, 3420, 3255, 3090, 2923, 2756, 2588, 2419, 2249, 2079, 1908, 
    1736, 1564, 1391, 1218, 1045, 871, 697, 523, 348, 174, 0, -174, -348, -523, -697, -871, 
    -1045, -1218, -1391, -1564, -1736, -1908, -2079, -2249, -2419, -2588, -2756, -2923, -3090, -3255, -3420, -3583, 
    -3746, -3907, -4067, -4226, -4384, -4540, -4695, -4848, -5000, -5150, -5299, -5446, -5592, -5736, -5878, -6018, 
    -6157, -6293, -6428, -6561, -6691, -6820, -6947, -7071, -7193, -7314, -7431, -7547, -7660, -7771, -7880, -7986, 
    -8090, -8192, -8290, -8387, -8480, -8572, -8660, -8746, -8829, -8910, -8988, -9063, -9135, -9205, -9272, -9336, 
    -9397, -9455, -9511, -9563, -9613, -9659, -9703, -9744, -9781, -9816, -9848, -9877, -9903, -9925, -9945, -9961, 
    -9975, -9986, -9994, -9998, -10000, -9998, -9994, -9986, -9975, -9961, -9945, -9925, -9903, -9877, -9848, -9816, 
    -9781, -9744, -9703, -9659, -9613, -9563, -9511, -9455, -9397, -9336, -9272, -9205, -9135, -9063, -8988, -8910, 
    -8829, -8746, -8660, -8572, -8480, -8387, -8290, -8192, -8090, -7986, -7880, -7771, -7660, -7547, -7431, -7314, 
    -7193, -7071, -6947, -6820, -6691, -6561, -6428, -6293, -6157, -6018, -5878, -5736, -5592, -5446, -5299, -5150, 
    -5000, -4848, -4695, -4540, -4384, -4226, -4067, -3907, -3746, -3583, -3420, -3255, -3090, -2923, -2756, -2588, 
    -2419, -2249, -2079, -1908, -1736, -1564, -1391, -1218, -1045, -871, -697, -523, -348, -174, 0, 174, 
    348, 523, 697, 871, 1045, 1218, 1391, 1564, 1736, 1908, 2079, 2249, 2419, 2588, 2756, 2923, 
    3090, 3255, 3420, 3583, 3746, 3907, 4067, 4226, 4384, 4540, 4695, 4848, 5000, 5150, 5299, 5446, 
    5592, 5736, 5878, 6018, 6157, 6293, 6428, 6561, 6691, 6820, 6947, 7071, 7193, 7314, 7431, 7547, 
    7660, 7771, 7880, 7986, 8090, 8192, 8290, 8387, 8480, 8572, 8660, 8746, 8829, 8910, 8988, 9063, 
    9135, 9205, 9272, 9336, 9397, 9455, 9511, 9563, 9613, 9659, 9703, 9744, 9781, 9816, 9848, 9877, 
    9903, 9925, 9945, 9961, 9975, 9986, 9994, 9998
};





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


void drawchar(char character, unsigned int startX, unsigned char startY) {
    int fontwidth = 4;
    int index;
        index = findcharindex(character);
        if (index != -1) {
            const unsigned short* nextchar = alphabet[index];
            int x, y;
            unsigned int scaledX, scaledY;
	    for (y = 0; y < fontwidth; y++) {   // iterate over Y-axis pixels (rows)
                for (x = 0; x < fontwidth; x++) { // for each X column, font_width pixels
                    if ((*nextchar) & (1 << (fontwidth - 1 - x))) {
                        scaledX = startX + x;
                        scaledY = startY + y;

                        // draw pixel using tgi_setpixel
                        tgi_setpixel(scaledX, scaledY);
                    }
                }
                nextchar++; // Move to the next row in the grid
            }
        } else {
            printf("character '%c' not found\n", character);
        }
 
        return;
}




void drawstring(const char* str, 
                unsigned int startX, 
                unsigned char startY) {
    while (*str != '\0') {
        drawchar(*str, startX, startY);
        startX += 5; // font1 4x4 needs 5 pixels for each char
        str++;
    }
}



void drawWrappedString(const char* text, 
                       unsigned char maxLineLength, 
                       unsigned char startX, 
                       unsigned char startY) {
  
    int fontwidth, fontheight;    
    const char* currentWord = text;
    unsigned int currentLength = 0;
    char currentWordCopy[20]; // max word size , TODO: things break if its too small
    unsigned int currentLineStartX = startX;

    while (*text != '\0') {
                 fontwidth = 5;
                 fontheight = 5;

        if (*text == ' ') { //if the current char is a space we jump 6 pixels on Y axis
            currentWordCopy[currentLength] = '\0'; // Null-terminate the string
            if (currentLineStartX + (currentLength * fontwidth) > startX + maxLineLength * fontwidth ) {
                // If adding the current word would exceed maxLineLength, start a new line
                startY += 7 ; //advance y axis if current char is ' ' space
                currentLineStartX = startX;
            }
            drawstring(currentWordCopy, currentLineStartX, startY);
            currentLineStartX += currentLength * fontwidth + 3; // affects X axis character spacing
            currentLength = 0;
        } else {
            currentWordCopy[currentLength] = *text;
            currentLength++;
        }
      
        text+=1;
    }

    // Draw the last word if needed
    if (currentLength > 0) {
        currentWordCopy[currentLength] = '\0'; // Null-terminate the string
        if (currentLineStartX + (currentLength * 7 ) > startX + maxLineLength * 7) {
           //  If adding the last word would exceed maxLineLength, start a new line
            startY += 7;
            currentLineStartX = startX;
        }
        drawstring(currentWordCopy, currentLineStartX, startY);
      //TODO: need to decide what to do if the word length is longer than the max length
    }
}







unsigned char toggle_clear = 0;




// vertices for 100x100x100 cube
signed long x0 = -50, y0 = -50, z0 = -50;
signed long x1 =  50, y1 = -50, z1 = -50;
signed long x2 =  50, y2 =  50, z2 = -50;
signed long x3 = -50, y3 =  50, z3 = -50;
signed long x4 = -50, y4 = -50, z4 =  50;
signed long x5 =  50, y5 = -50, z5 =  50;
signed long x6 =  50, y6 =  50, z6 =  50;
signed long x7 = -50, y7 =  50, z7 =  50;

//starting angles 0-360
unsigned int rotX = 0;
unsigned int rotY = 0;
unsigned int rotZ = 0;


void rotate_x(long *y, long *z, long angle) {
    signed long tempY = *y;
    signed long tempZ = *z;
    *y = (tempY * cosine[angle] - tempZ * sine[angle]) / 10000L;
    *z = (tempY * sine[angle] + tempZ * cosine[angle]) / 10000L;
}

void rotate_y(long *x, long *z, long angle) {
    signed long tempX = *x;
    signed long tempZ = *z;
    *x = (tempX * cosine[angle] + tempZ * sine[angle]) / 10000L;
    *z = (-tempX * sine[angle] + tempZ * cosine[angle]) / 10000L;
}

void rotate_z(long *x, long *y, long angle) {
    signed long tempX = *x;
    signed long tempY = *y;
    *x = (tempX * cosine[angle] - tempY * sine[angle]) / 10000L;
    *y = (tempX * sine[angle] + tempY * cosine[angle]) / 10000L;
}


void draw_cube() {
    signed long tx0 = x0, ty0 = y0, tz0 = z0;
    signed long tx1 = x1, ty1 = y1, tz1 = z1;
    signed long tx2 = x2, ty2 = y2, tz2 = z2;
    signed long tx3 = x3, ty3 = y3, tz3 = z3;
    signed long tx4 = x4, ty4 = y4, tz4 = z4;
    signed long tx5 = x5, ty5 = y5, tz5 = z5;
    signed long tx6 = x6, ty6 = y6, tz6 = z6;
    signed long tx7 = x7, ty7 = y7, tz7 = z7;

    rotate_x(&ty0, &tz0, rotX); rotate_y(&tx0, &tz0, rotY); rotate_z(&tx0, &ty0, rotZ);
    rotate_x(&ty1, &tz1, rotX); rotate_y(&tx1, &tz1, rotY); rotate_z(&tx1, &ty1, rotZ);
    rotate_x(&ty2, &tz2, rotX); rotate_y(&tx2, &tz2, rotY); rotate_z(&tx2, &ty2, rotZ);
    rotate_x(&ty3, &tz3, rotX); rotate_y(&tx3, &tz3, rotY); rotate_z(&tx3, &ty3, rotZ);
    rotate_x(&ty4, &tz4, rotX); rotate_y(&tx4, &tz4, rotY); rotate_z(&tx4, &ty4, rotZ);
    rotate_x(&ty5, &tz5, rotX); rotate_y(&tx5, &tz5, rotY); rotate_z(&tx5, &ty5, rotZ);
    rotate_x(&ty6, &tz6, rotX); rotate_y(&tx6, &tz6, rotY); rotate_z(&tx6, &ty6, rotZ);
    rotate_x(&ty7, &tz7, rotX); rotate_y(&tx7, &tz7, rotY); rotate_z(&tx7, &ty7, rotZ);

    if (toggle_clear) {
        //tgi_clear();  // Call tgi_clear if the flag is set
     tgi_setcolor (COLOR_BLACK);
     tgi_bar (5, 5, 190, 190);
     tgi_setcolor (COLOR_WHITE);
    }

    tgi_line(tx0 + 100, ty0 + 100, tx1 + 100, ty1 + 100);
    tgi_line(tx1 + 100, ty1 + 100, tx2 + 100, ty2 + 100);
    tgi_line(tx2 + 100, ty2 + 100, tx3 + 100, ty3 + 100);
    tgi_line(tx3 + 100, ty3 + 100, tx0 + 100, ty0 + 100);

    tgi_line(tx4 + 100, ty4 + 100, tx5 + 100, ty5 + 100);
    tgi_line(tx5 + 100, ty5 + 100, tx6 + 100, ty6 + 100);
    tgi_line(tx6 + 100, ty6 + 100, tx7 + 100, ty7 + 100);
    tgi_line(tx7 + 100, ty7 + 100, tx4 + 100, ty4 + 100);

    tgi_line(tx0 + 100, ty0 + 100, tx4 + 100, ty4 + 100);
    tgi_line(tx1 + 100, ty1 + 100, tx5 + 100, ty5 + 100);
    tgi_line(tx2 + 100, ty2 + 100, tx6 + 100, ty6 + 100);
    tgi_line(tx3 + 100, ty3 + 100, tx7 + 100, ty7 + 100);
}





void itoa_custom(int num, char* str) {
    int i = 0, rem;    // Declare variables at the beginning
    int start, end;    // Declare start and end here as well

    if (num == 0) {
        str[i++] = '0';
    } else {
        while (num != 0) {
            rem = num % 10;
            str[i++] = rem + '0';
            num = num / 10;
        }
    }
    str[i] = '\0';

    start = 0;
    end = i - 1;

    // Reverse the string
    while (start < end) {
        char temp = str[start];
        str[start] = str[end];
        str[end] = temp;
        start++;
        end--;
    }
}





char* msgcat(char* message, int num) {
    static char result[40];
    int i = 0;
    char snum[10];
    int j = 0;

    itoa_custom(num, snum);

    while (message[i] != '\0') {
        result[i] = message[i];
        i++;
    }

    while (snum[j] != '\0') {
        result[i++] = snum[j++];
    }

    result[i] = '\0';  
    return result;
}





int main() {
    const char* mystring1 = "DEBUG MODE - painting half of screen to clear, its slow";
    const char* mystring2 = "CUBE ROTATE SPACE BAR TOGGLES SCREEN WIPE AFTER EACH ROTATION ";
 
    int ninecount; 
    char Border;
    char ch;

    char xxmessage[20] = "XX ROTATION - ";
    char yymessage[20] = "YY ROTATION - ";
    char zzmessage[20] = "ZZ ROTATION - ";
    char* newoutput;
    tgi_install(tgi_static_stddrv);  
    tgi_init();      
    tgi_clear();
    
    tgi_setcolor (COLOR_WHITE);

  
    rotX = 15;  
    rotY = 110;
    rotZ = 85;
    drawWrappedString(mystring2, 20, 200, 14); 
    newoutput = msgcat(xxmessage, rotX);  // For rotX
    drawWrappedString(newoutput, 20, 200, 144); 
    newoutput = msgcat(yymessage, rotY);  // For rotX
    drawWrappedString(newoutput, 20, 200, 150); 
    newoutput = msgcat(zzmessage, rotZ);  // For rotX
    drawWrappedString(newoutput, 20, 200, 156); 
  
  
      while (1) {
        if (toggle_clear == 1) {
          Border = bordercolor (COLOR_BLUE);
          //tgi_clear();
              drawWrappedString(mystring1, 20, 200, 14); 
        }
        
        ninecount += 1;
        
                if (toggle_clear == 0) {
          Border = bordercolor (COLOR_RED);
                  
          
        }
        
        if (ninecount >= 6){
         // tgi_clear();
          ninecount = 0;
        };


        if (kbhit()) {
          tgi_clear();
        ch = cgetc();  // Only call cgetc if a key has been pressed
                  if (ch == ' ') { 
            toggle_clear = !toggle_clear;
                    
        }
}      
        
        
        tgi_setcolor (COLOR_WHITE);
        
        rotX += 13;
        //rotY += 3;
        //rotZ += 1;
        
if (rotX >= 359) {
    rotX = 0;
    rotY += 13;
    tgi_clear();
drawWrappedString(newoutput, 20, 200, 144); 
newoutput = msgcat(yymessage, rotY);  // For rotX
drawWrappedString(newoutput, 20, 200, 150); 
newoutput = msgcat(zzmessage, rotZ);  // For rotX
drawWrappedString(newoutput, 20, 200, 156); 
  

}
if (rotY >= 359) {
rotY = 0;
rotZ += 13;
//tgi_clear();  // Call tgi_clear() here
}
if (rotZ >= 359) {
    rotZ = 0;
//    tgi_clear();  // Call tgi_clear() here
}
tgi_setcolor (COLOR_BLACK);
tgi_bar(260,144,280,147);
tgi_setcolor (COLOR_WHITE);
newoutput = msgcat(xxmessage, rotX);  // For rotX
drawWrappedString(newoutput, 20, 200, 144); 
        
        
        draw_cube();
      }
 

    return 0;
}