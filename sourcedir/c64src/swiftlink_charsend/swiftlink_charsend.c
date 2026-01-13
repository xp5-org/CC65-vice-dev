#include <stdio.h>
#include <cbm.h>
#include <serial.h>
#include <conio.h>
//#include <peekpoke.h>
extern char c64_swlink;
unsigned char okstatus;

static void install_serial(){
  unsigned char r;

    r = ser_install(&c64_swlink);
    if (r != SER_ERR_OK) {
        printf("Failed to install serial driver, error code: %u\n", r);
    }
    printf("Serial driver installed successfully\n");

}

void open_serial(){
    unsigned char r;
    // other bauds dont work with vice emulator idk 
    struct ser_params params = {
        SER_BAUD_38400,
        SER_BITS_8,
        SER_STOP_1,
        SER_PAR_NONE,
        SER_HS_HW
        };
    r = ser_open(&params);
    if (r == SER_ERR_OK) {
        printf("Serial port opened \n");
        okstatus = 1;
    } else {
        printf("Failed, code: %u\n", r);
        okstatus = 0;
    }
}


void print_ser_status(void){
    unsigned char hw_status;
    unsigned char r;
    gotoxy(0, 15); // col , row
    r = ser_status(&hw_status);
    
    if (r != SER_ERR_OK) {
        printf("Could not get status: %u  \n", r);
        return;
    }

    printf("Status Byte: $%02X      \n", hw_status);
    printf("Parity:  %s\n", (hw_status & SER_STATUS_PE)  ? "ERR " : "OK  ");
    printf("Framing: %s\n", (hw_status & SER_STATUS_FE)  ? "ERR " : "OK  ");
    printf("Overrun: %s\n", (hw_status & SER_STATUS_OE)  ? "ERR " : "OK  ");
    
    if (hw_status & SER_STATUS_DCD) printf("DCD: No Carrier        \n");
    else                            printf("DCD: Carrier Detect OK \n");

    if (hw_status & SER_STATUS_DSR) printf("DSR: Not Ready         \n");
    else                            printf("DSR: Data Set Ready OK \n");
}   



void ser_puts(const char *s){
    while (*s) {
        while (ser_put(*s) == SER_ERR_OVERFLOW)
        ;
        s++;
    }
}


int main(void){
    char status;
    char charbuffer;
    okstatus = 0;
    install_serial();
    open_serial();
    print_ser_status();

    if (okstatus == 0) {
        printf("Status failed \n");
        

    }
    if (okstatus == 1) {
        printf("Status good \n");
        ser_puts("this is a test string");
        printf("String sent\n");
    }


    
    while (1) {
            status = ser_get(&charbuffer);
            if (status == SER_ERR_OK) {
                if (charbuffer == 0x0D) {
                    cputc('\r');
                    cputc('\n');
                } else {
                    cputc(charbuffer);
                }
            }
        }

    return 0;
}
