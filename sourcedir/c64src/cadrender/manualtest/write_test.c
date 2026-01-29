#include <cbm.h>
#include <stdio.h>

// tests writing binary data to disk

/* Struct definitions */
typedef struct { int x, y, z; } Point;
typedef struct { int a, b, c; } Face;

typedef struct {
    int num_points;
    int num_tris;
    Point *points;
    Face *tris;
} Model;

typedef struct {
    Model *model;
    int ox, oy, oz;
    int rx, ry, rz;
    int id;
} SceneNode;

/* Static test data */
static Point points0[2] = {{10,20,30},{40,50,60}};
static Face tris0[1] = {{0,1,0}};
static Model model0 = {2, 1, points0, tris0};

static SceneNode scene_nodes[2] = {
    {&model0, 0,0,0, 0,0,0, 1},
    {&model0, 100,200,300, 0,90,0, 2}
};

int main(void)
{
    unsigned int channel = 1;       /* secondary address for sequential file */
    unsigned int diskdeviceid = 8;  /* typical disk device */
    int written;
    unsigned char load_addr[2] = {0x00, 0x08};
    unsigned char buf[256];
    unsigned char *ptr;
    int i;

    /* Build a simple binary representation: [load_addr][num_nodes][nodes...] */
    ptr = buf;

    /* C64 BASIC load address */
    *ptr++ = load_addr[0];
    *ptr++ = load_addr[1];

    /* Number of scene nodes */
    *ptr++ = (unsigned char)(2 & 0xFF);
    *ptr++ = (unsigned char)((2 >> 8) & 0xFF);

    /* Encode each scene node: id, position, rotation, model index (1 byte) */
    for (i=0; i<2; i++) {
        SceneNode *n = &scene_nodes[i];
        *ptr++ = (unsigned char)(n->id & 0xFF);
        *ptr++ = (unsigned char)((n->id >> 8) & 0xFF);

        *ptr++ = (unsigned char)(n->ox & 0xFF);
        *ptr++ = (unsigned char)((n->ox >> 8) & 0xFF);
        *ptr++ = (unsigned char)(n->oy & 0xFF);
        *ptr++ = (unsigned char)((n->oy >> 8) & 0xFF);
        *ptr++ = (unsigned char)(n->oz & 0xFF);
        *ptr++ = (unsigned char)((n->oz >> 8) & 0xFF);

        *ptr++ = (unsigned char)(n->rx & 0xFF);
        *ptr++ = (unsigned char)((n->rx >> 8) & 0xFF);
        *ptr++ = (unsigned char)(n->ry & 0xFF);
        *ptr++ = (unsigned char)((n->ry >> 8) & 0xFF);
        *ptr++ = (unsigned char)(n->rz & 0xFF);
        *ptr++ = (unsigned char)((n->rz >> 8) & 0xFF);

        *ptr++ = 0; /* model index, 0 for model0 */
    }

    /* Open file */
    if (cbm_open(channel, diskdeviceid, channel, "SCENETEST,P,W") != 0) {
        printf("open error\n");
        return 1;
    }

    /* Write buffer (ptr - buf = number of bytes used) */
    written = cbm_write(channel, buf, (unsigned int)(ptr - buf));
    if (written != (ptr - buf)) {
        printf("write error: %d/%u\n", written, (unsigned int)(ptr - buf));
        cbm_close(channel);
        return 1;
    }

    cbm_close(channel);
    printf("scene binary written successfully\n");
    return 0;
}
