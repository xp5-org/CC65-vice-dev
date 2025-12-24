//https://www.cc65.org/doc/funcref-18.html
#include <c64.h>
#include <conio.h>
#include <em.h>
#include <stdio.h>

extern char c64_reu;




void print_kb(unsigned long kb) {
    gotoxy(0, 15); // column 0, row 5
    if (kb >= 1000) cputc((kb / 1000) % 10 + '0');
    if (kb >= 100)  cputc((kb / 100) % 10 + '0');
    if (kb >= 10)   cputc((kb / 10) % 10 + '0');
    cputc(kb % 10 + '0');
    cputs(" KB written");
}




unsigned int em_kb_available(void) {
    unsigned int pages = em_pagecount();
    return pages / 4;
}

unsigned long fill_reu_pattern(void) {
    unsigned long pages;
    unsigned long page;
    unsigned long pages_written;
    unsigned int i;
    unsigned char *p;

    pages = (unsigned long)em_pagecount();
    pages_written = 0;

    // setup repeating fill pattern
    for (page = 0; page < pages; ++page) {
        p = (unsigned char *)em_use((unsigned)page);
        for (i = 0; i < 256; ++i) {
            if ((i & 3) == 0) p[i] = 0xDE;
            else if ((i & 3) == 1) p[i] = 0xAD;
            else if ((i & 3) == 2) p[i] = 0xBE;
            else p[i] = 0xEF;
        }
        em_commit();
        ++pages_written;
        if ((pages_written & 3) == 0) {
            print_kb(pages_written >> 2);
            }
    }
    printf("\n\r");
        return pages_written >> 2;
    }



void dump_reu_pages(void) {
    unsigned long pages;
    unsigned long page;
    unsigned int i;
    unsigned char *p;

    pages = (unsigned long)em_pagecount();

    for (page = 0; page < pages; ++page) {
        p = (unsigned char *)em_map((unsigned)page);

        printf("Page %lu:\n", page);

        for (i = 0; i < 256; ++i) {
            printf("%02X ", p[i]);
            if ((i & 15) == 15) {
                printf("\n");
            }
        }

        printf("\n");
    }
}









int main(void) {
    unsigned char result = em_install(&c64_reu);

    if (result != 0) {
        printf("Failed to install REU driver, error code: %u\n", result);
        return 1;
    }

    printf("REU driver installed successfully.\n");
    printf("Available extended memory: %u KB\n", em_kb_available());

    fill_reu_pattern();

    printf("REU filled with DEADBEEF pattern\n");

    
    //dump_reu_pages();

    return 0;
}
