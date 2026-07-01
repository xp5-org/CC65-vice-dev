#include <gem.h>
#include <osbind.h>
#include <stdio.h>

short vdi_handle;
short work_in[11];
short work_out[57];

static unsigned long rng_state = 12345UL;

static unsigned long lcg_rand(void)
{
    rng_state = rng_state * 1664525UL + 1013904223UL;
    return rng_state;
}

/* read the 200Hz system tick counter (must run in supervisor mode) */
static long read_hz200(void)
{
    return *((volatile long *)0x4baL);
}

void draw_status(short scr_w, short scr_h, short rps)
{
    short pxy[4];
    char buf[48];

    sprintf(buf, "rectangles per second: %d", rps);

    /* clear a bar across the lower-left corner */
    pxy[0] = 0;
    pxy[1] = scr_h - 16;
    pxy[2] = scr_w - 1;
    pxy[3] = scr_h - 1;
    vsf_interior(vdi_handle, 1);
    vsf_color(vdi_handle, 0);
    vr_recfl(vdi_handle, pxy);

    /* draw the status text in colour 1 on the cleared bar */
    vst_color(vdi_handle, 1);
    v_gtext(vdi_handle, 4, scr_h - 4, buf);
}

void open_vwork(void)
{
    short i, dummy;
    vdi_handle = graf_handle(&dummy, &dummy, &dummy, &dummy);
    for (i = 0; i < 10; work_in[i++] = 1);
    work_in[10] = 2;
    v_opnvwk(work_in, &vdi_handle, work_out);
}

void draw_random_rect(short scr_w, short scr_h, short num_colors)
{
    short pxy[4];
    short x, y, w, h;
    short color;

    /* seed with system clock for first call variation */
    x = (short)(lcg_rand() % (unsigned long)(scr_w - 20));
    y = (short)(lcg_rand() % (unsigned long)(scr_h - 20));
    w = (short)(lcg_rand() % (unsigned long)(scr_w / 4)) + 10;
    h = (short)(lcg_rand() % (unsigned long)(scr_h / 4)) + 10;

    /* clamp to screen */
    if (x + w > scr_w) w = scr_w - x;
    if (y + h > scr_h) h = scr_h - y;

    color = (short)(lcg_rand() % (unsigned long)num_colors);

    pxy[0] = x;
    pxy[1] = y;
    pxy[2] = x + w - 1;
    pxy[3] = y + h - 1;

    vsf_interior(vdi_handle, 1);
    vsf_color(vdi_handle, color);
    vr_recfl(vdi_handle, pxy);
}

int main(void)
{
    short ap_id, done = 0;
    short msg[8];
    short ev, timer_ms = 1;
    short scr_w, scr_h, num_colors;
    short mx, my, mb, ks, kc, br;
    long last_ticks, now_ticks, elapsed;
    long rects_in_window = 0;
    short rps = 0;

    ap_id = appl_init();
    if (ap_id == -1) return 0;

    open_vwork();

    /* screen dimensions and colour count from VDI */
    scr_w = work_out[0] + 1;
    scr_h = work_out[1] + 1;
    num_colors = work_out[13];
    if (num_colors < 2) num_colors = 2;

    /* seed rng with system time */
    rng_state ^= (unsigned long)Tgettime();

    graf_mouse(M_OFF, 0L);

    last_ticks = Supexec(read_hz200);
    draw_status(scr_w, scr_h, rps);

    while (!done) {
        ev = evnt_multi(MU_MESAG | MU_TIMER | MU_KEYBD,
                        0, 0, 0,
                        0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0,
                        msg,
                        (unsigned long)timer_ms,
                        &mx, &my, &mb, &ks, &kc, &br);

        if (ev & MU_TIMER) {
            draw_random_rect(scr_w, scr_h, num_colors);
            rects_in_window++;

            /* once a second, compute and show the real draw rate */
            now_ticks = Supexec(read_hz200);
            elapsed = now_ticks - last_ticks;
            if (elapsed >= 200) {
                rps = (short)((rects_in_window * 200L) / elapsed);
                draw_status(scr_w, scr_h, rps);
                rects_in_window = 0;
                last_ticks = now_ticks;
            }
        }

        if (ev & MU_KEYBD) {
            /* any key press exits */
            done = 1;
        }

        if (ev & MU_MESAG) {
            if (msg[0] == WM_CLOSED) done = 1;
        }
    }

    graf_mouse(ARROW, 0L);
    v_clsvwk(vdi_handle);
    appl_exit();
    return 0;
}
