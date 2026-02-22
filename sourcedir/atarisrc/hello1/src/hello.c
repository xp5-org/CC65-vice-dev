#include <gem.h>
#include <osbind.h>



short vdi_handle;
short work_in[11];
short work_out[57];

#define M_BAR    0
#define M_ROOT   1
#define M_FILE   2
#define M_DROP   3
#define M_ABOUT  4
#define M_QUIT   5

OBJECT menu_tree[] = {
    { -1, 1, 1, G_BOX,    OF_NONE, OS_NORMAL, 0x00021100L, 0, 0, 80, 1 },   // root
    { 0, 2, 2, G_IBOX,    OF_NONE, OS_NORMAL, 0L, 0, 0, 80, 1 },             // menu bar container
    { 1, 3, -1, G_TITLE,  OF_NONE, OS_NORMAL, (long)"File", 0, 0, 6, 1 },    // File title
    { 2, 4, -1, G_BOX,    OF_NONE, OS_NORMAL, 0L, 0, 0, 16, 2 },             // File dropdown box (width=16, height=2)
    { 3, -1, -1, G_STRING, OF_SELECTABLE, OS_NORMAL, (long)"About...", 0, 0, 15, 1 },
    { 3, -1, -1, G_STRING, OF_SELECTABLE, OS_NORMAL, (long)"Quit", 0, 1, 15, 1 }
};


void open_vwork(void)
{
    short i, dummy;
    vdi_handle = graf_handle(&dummy, &dummy, &dummy, &dummy);
    for (i = 0; i < 10; work_in[i++] = 1);
    work_in[10] = 2;
    v_opnvwk(work_in, &vdi_handle, work_out);
}

void draw_content(short wh, short cx, short cy, short cw, short ch)
{
    short pxy[4];
    short wx, wy, ww, wh_inner;

    wind_get(wh, WF_WORKXYWH, &wx, &wy, &ww, &wh_inner);

    pxy[0] = cx;
    pxy[1] = cy;
    pxy[2] = cx + cw - 1;
    pxy[3] = cy + ch - 1;
    vs_clip(vdi_handle, 1, pxy);

    vsf_interior(vdi_handle, 1);
    vsf_color(vdi_handle, 0);
    vr_recfl(vdi_handle, pxy);

    v_gtext(vdi_handle, wx + 10, wy + 20, "Test3!");

    vs_clip(vdi_handle, 0, pxy);
}

void handle_redraw(short wh, GRECT *dirty)
{
    GRECT v;
    wind_get(wh, WF_FIRSTXYWH, &v.g_x, &v.g_y, &v.g_w, &v.g_h);
    while (v.g_w && v.g_h) {
        if (rc_intersect(dirty, &v)) {
            draw_content(wh, v.g_x, v.g_y, v.g_w, v.g_h);
        }
        wind_get(wh, WF_NEXTXYWH, &v.g_x, &v.g_y, &v.g_w, &v.g_h);
    }
}

int main(void)
{
    char *s = "Hello\n";
    short ap_id, wi_handle, msg[8], done = 0, i;
    short x, y, w, h;
    GRECT rect;
    short flags = NAME | CLOSER | MOVER | SIZER;

    ap_id = appl_init();
    if (ap_id == -1) return 0;

    for (i = 0; i <= 5; i++) rsrc_obfix(menu_tree, i);

    wind_calc(0, flags, 50, 50, 200, 100, &x, &y, &w, &h);
    wi_handle = wind_create(flags, x, y, w, h);
    wind_set(wi_handle, WF_NAME, (short)((long)"Interactive" >> 16), (short)((long)"Interactive" & 0xFFFF), 0, 0);
    wind_open(wi_handle, x, y, w, h);

    menu_bar(menu_tree, 1);
    open_vwork();
    graf_mouse(0, 0);
    Rsconf(1, 0, 0x88, -1, -1, -1);
        while (*s) {
            while (Bcostat(1) == 0);
            Bconout(1, *s++);
        }

    while (!done) {
        evnt_mesag(msg);
        switch (msg[0]) {
            case MN_SELECTED:
                if (msg[4] == M_QUIT) done = 1;
                else if (msg[4] == M_ABOUT) form_alert(1, "[1][ GEM Hello World ][ OK ]");
                menu_tnormal(menu_tree, msg[3], 1);
                break;
            case WM_REDRAW:
                rect.g_x = msg[4]; rect.g_y = msg[5];
                rect.g_w = msg[6]; rect.g_h = msg[7];
                wind_update(1);
                handle_redraw(msg[3], &rect);
                wind_update(0);
                break;
            case WM_MOVED:
            case WM_SIZED:
                wind_set(msg[3], WF_CURRXYWH, msg[4], msg[5], msg[6], msg[7]);
                break;
            case WM_CLOSED:
                done = 1;
                break;
        }
    }

    menu_bar(menu_tree, 0);
    wind_close(wi_handle);
    wind_delete(wi_handle);
    v_clsvwk(vdi_handle);
    appl_exit();
    return 0;
}
