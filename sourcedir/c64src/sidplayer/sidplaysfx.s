
; music and SFX from GoatTracker 2 sample files
; http://sourceforge.net/projects/goattracker2

;.segment "DATA"

;_sid_playing: .byte $00

.segment "SIDFILE"

.incbin "sidmusic1.bin"

.segment "LOWCODE"

.global _sid_init, _sid_update, _sid_sfx
.global _sid_start, _sid_stop, _sid_playing

_sid_init:
        jmp $1000

_sid_update:
;	bit _sid_playing
        bpl @noplay
	jmp $1003
@noplay:
        rts

_sid_sfx:
	tax
        ldx #$0e           ;Channel index in X
        jmp $1006          ;(0, 7 or 14)

_sid_start:
	lda #$80
        bne skipstop
_sid_stop:
	lda #$00
        sta $d418
skipstop:
;        sta _sid_playing
        rts

