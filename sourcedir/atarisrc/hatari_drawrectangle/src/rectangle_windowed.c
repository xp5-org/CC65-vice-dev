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

void open_vwork(void)
{
    short i, dummy;
    vdi_handle = graf_handle(&dummy, &dummy, &dummy, &dummy);
    for (i = 0; i < 10; work_in[i++] = 1);
    work_in[10] = 2;
    v_opnvwk(work_in, &vdi_handle, work_out);
}

/* clip subsequent VDI output to the window's work area */
static void set_clip(GRECT *work)
{
    short pxy[4];
    pxy[0] = work->g_x;
    pxy[1] = work->g_y;
    pxy[2] = work->g_x + work->g_w - 1;
    pxy[3] = work->g_y + work->g_h - 1;
    vs_clip(vdi_handle, 1, pxy);
}

void draw_status(GRECT *work, short num_colors, short rps)
{
    short pxy[4];
    char buf[48];

    sprintf(buf, "rectangles per second: %d", rps);

    /* clear a bar across the bottom of the work area */
    pxy[0] = work->g_x;
    pxy[1] = work->g_y + work->g_h - 16;
    pxy[2] = work->g_x + work->g_w - 1;
    pxy[3] = work->g_y + work->g_h - 1;
    vsf_interior(vdi_handle, 1);
    vsf_color(vdi_handle, 0);
    vr_recfl(vdi_handle, pxy);

    /* draw the status text in colour 1 on the cleared bar */
    vst_color(vdi_handle, 1);
    v_gtext(vdi_handle, work->g_x + 4, work->g_y + work->g_h - 4, buf);
}

void draw_random_rect(GRECT *work, short num_colors)
{
    short pxy[4];
    short x, y, w, h;
    short color;

    /* pick a position and size within the window work area */
    if (work->g_w < 20 || work->g_h < 20) return;

    x = work->g_x + (short)(lcg_rand() % (unsigned long)(work->g_w - 10));
    y = work->g_y + (short)(lcg_rand() % (unsigned long)(work->g_h - 10));
    w = (short)(lcg_rand() % (unsigned long)(work->g_w / 4)) + 10;
    h = (short)(lcg_rand() % (unsigned long)(work->g_h / 4)) + 10;

    /* clamp to the work area */
    if (x + w > work->g_x + work->g_w) w = work->g_x + work->g_w - x;
    if (y + h > work->g_y + work->g_h) h = work->g_y + work->g_h - y;

    color = (short)(lcg_rand() % (unsigned long)num_colors);

    pxy[0] = x;
    pxy[1] = y;
    pxy[2] = x + w - 1;
    pxy[3] = y + h - 1;

    vsf_interior(vdi_handle, 1);
    vsf_color(vdi_handle, color);
    vr_recfl(vdi_handle, pxy);
}

/* clear the dirty portions of the window to the background colour */
void handle_redraw(short wh, GRECT *dirty)
{
    GRECT v;
    short pxy[4];

    wind_update(BEG_UPDATE);
    wind_get(wh, WF_FIRSTXYWH, &v.g_x, &v.g_y, &v.g_w, &v.g_h);
    while (v.g_w && v.g_h) {
        if (rc_intersect(dirty, &v)) {
            pxy[0] = v.g_x;
            pxy[1] = v.g_y;
            pxy[2] = v.g_x + v.g_w - 1;
            pxy[3] = v.g_y + v.g_h - 1;
            vs_clip(vdi_handle, 1, pxy);
            vsf_interior(vdi_handle, 1);
            vsf_color(vdi_handle, 0);
            vr_recfl(vdi_handle, pxy);
        }
        wind_get(wh, WF_NEXTXYWH, &v.g_x, &v.g_y, &v.g_w, &v.g_h);
    }
    wind_update(END_UPDATE);
}

int main(void)
{
    short ap_id, done = 0;
    short msg[8];
    short ev, timer_ms = 1;
    short num_colors;
    short mx, my, mb, ks, kc, br;
    short x, y, w, h, wi_handle;
    short flags = NAME | CLOSER | MOVER | SIZER | FULLER;
    GRECT work, dirty;
    long last_ticks, now_ticks, elapsed;
    long rects_in_window = 0;
    short rps = 0;

    ap_id = appl_init();
    if (ap_id == -1) return 0;

    open_vwork();

    num_colors = work_out[13];
    if (num_colors < 2) num_colors = 2;

    /* seed rng with system time */
    rng_state ^= (unsigned long)Tgettime();

    /* create a window covering most of the desktop */
    wind_get(0, WF_WORKXYWH, &x, &y, &w, &h);
    wind_calc(WC_BORDER, flags, x + 20, y + 20, w - 40, h - 40, &x, &y, &w, &h);
    wi_handle = wind_create(flags, x, y, w, h);
    wind_set(wi_handle, WF_NAME,
             (short)((long)"Rectangles (windowed)" >> 16),
             (short)((long)"Rectangles (windowed)" & 0xFFFF), 0, 0);
    wind_open(wi_handle, x, y, w, h);

    wind_get(wi_handle, WF_WORKXYWH, &work.g_x, &work.g_y, &work.g_w, &work.g_h);

    last_ticks = Supexec(read_hz200);

    while (!done) {
        ev = evnt_multi(MU_MESAG | MU_TIMER | MU_KEYBD,
                        0, 0, 0,
                        0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0,
                        msg,
                        (unsigned long)timer_ms,
                        &mx, &my, &mb, &ks, &kc, &br);

        if (ev & MU_TIMER) {
            wind_update(BEG_UPDATE);
            set_clip(&work);
            draw_random_rect(&work, num_colors);
            rects_in_window++;

            /* once a second, compute and show the real draw rate */
            now_ticks = Supexec(read_hz200);
            elapsed = now_ticks - last_ticks;
            if (elapsed >= 200) {
                rps = (short)((rects_in_window * 200L) / elapsed);
                draw_status(&work, num_colors, rps);
                rects_in_window = 0;
                last_ticks = now_ticks;
            }
            vs_clip(vdi_handle, 0, (short *)&work);
            wind_update(END_UPDATE);
        }

        if (ev & MU_KEYBD) {
            /* any key press exits */
            done = 1;
        }

        if (ev & MU_MESAG) {
            switch (msg[0]) {
                case WM_REDRAW:
                    dirty.g_x = msg[4];
                    dirty.g_y = msg[5];
                    dirty.g_w = msg[6];
                    dirty.g_h = msg[7];
                    handle_redraw(msg[3], &dirty);
                    break;
                case WM_MOVED:
                case WM_SIZED:
                    wind_set(msg[3], WF_CURRXYWH,
                             msg[4], msg[5], msg[6], msg[7]);
                    wind_get(msg[3], WF_WORKXYWH,
                             &work.g_x, &work.g_y, &work.g_w, &work.g_h);
                    break;
                case WM_FULLED:
                    wind_get(msg[3], WF_FULLXYWH, &x, &y, &w, &h);
                    wind_set(msg[3], WF_CURRXYWH, x, y, w, h);
                    wind_get(msg[3], WF_WORKXYWH,
                             &work.g_x, &work.g_y, &work.g_w, &work.g_h);
                    break;
                case WM_CLOSED:
                    done = 1;
                    break;
            }
        }
    }

    wind_close(wi_handle);
    wind_delete(wi_handle);
    v_clsvwk(vdi_handle);
    appl_exit();
    return 0;
}
