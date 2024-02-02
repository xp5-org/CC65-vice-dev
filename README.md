vi hello.s
cc65 test.c #C to assembly
ca65 -t c64 test.s # assembly to object
ld65 -t c64 test.o -o test c64.lib # object to .prg
c1541 -format "disk,00" d64 disk.d64 #makle new disk
c1541 -attach disk.d64 -write test test,p #put on disk