#include <conio.h>
#include <stdio.h>
#include <cbm_petscii_charmap.h>
#include <stdint.h>




void myprint(unsigned char y, const char* s) {
    unsigned int addr = 1024 + y * 40;
    while (*s) {
        *(unsigned char*)addr = *s++;
        addr++;
    }
}


void main(void) {
    uint16_t start;
    uint16_t end;
    uint16_t total;
  
    volatile uint8_t* cia1_timer_a_lo = (uint8_t*)0xdc04;
    volatile uint8_t* cia1_timer_a_hi = (uint8_t*)0xdc05;
    volatile uint8_t* cia1_control    = (uint8_t*)0xdc0e;

    clrscr();

    *cia1_control = 0x00;
    *cia1_timer_a_lo = 0xff;
    *cia1_timer_a_hi = 0xff;
    *cia1_control = 0x11;
    start = *cia1_timer_a_lo | (*cia1_timer_a_hi << 8);
cputc('a');
    end = *cia1_timer_a_lo | (*cia1_timer_a_hi << 8);
    *cia1_control = 0x00;
    total = start - end;
    printf("\ncputc cycles: %u\n", total);
  
    *cia1_control = 0x00;
    *cia1_timer_a_lo = 0xff;
    *cia1_timer_a_hi = 0xff;
    *cia1_control = 0x11;
    start = *cia1_timer_a_lo | (*cia1_timer_a_hi << 8);
printf("a");
    end = *cia1_timer_a_lo | (*cia1_timer_a_hi << 8);
    *cia1_control = 0x00;
    total = start - end;
    printf("\nprintf cycles: %u\n", total);
  
    *cia1_control = 0x00;
    *cia1_timer_a_lo = 0xff;
    *cia1_timer_a_hi = 0xff;
    *cia1_control = 0x11;
    start = *cia1_timer_a_lo | (*cia1_timer_a_hi << 8);
myprint(0,"a");
    end = *cia1_timer_a_lo | (*cia1_timer_a_hi << 8);
    *cia1_control = 0x00;
    total = start - end;
    printf("\nmyprint cycles: %u\n", total);
  
    *cia1_control = 0x00;
    *cia1_timer_a_lo = 0xff;
    *cia1_timer_a_hi = 0xff;
    *cia1_control = 0x11;
    start = *cia1_timer_a_lo | (*cia1_timer_a_hi << 8);
putchar('a');
    end = *cia1_timer_a_lo | (*cia1_timer_a_hi << 8);
    *cia1_control = 0x00;
    total = start - end;
    printf("\nputchar cycles: %u\n", total);
}