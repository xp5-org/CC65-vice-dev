#include <conio.h>
#include <tgi.h>

#define COLOR_BACK      TGI_COLOR_BLACK
#define COLOR_FORE      TGI_COLOR_WHITE
#define MAX_POINTS      182
#define MAX_FACES       122
#define MAX_SCENE_FACES 184

/* Sine/Cosine Tables (Provided in your snippet) */

static const int sine[] = {
    0, 4, 9, 13, 18, 22, 27, 31, 35, 40, 44, 49, 53, 58, 62, 66, 
    71, 75, 79, 83, 88, 92, 96, 100, 104, 108, 112, 116, 120, 124, 128, 132, 
    136, 139, 143, 147, 150, 154, 158, 161, 165, 168, 171, 175, 178, 181, 184, 187, 
    190, 193, 196, 199, 202, 204, 207, 210, 212, 215, 217, 219, 222, 224, 226, 228, 
    230, 232, 234, 236, 237, 239, 241, 242, 243, 245, 246, 247, 248, 249, 250, 251, 
    252, 253, 254, 254, 255, 255, 255, 256, 256, 256, 256, 256, 256, 256, 255, 255, 
    255, 254, 254, 253, 252, 251, 250, 249, 248, 247, 246, 245, 243, 242, 241, 239, 
    237, 236, 234, 232, 230, 228, 226, 224, 222, 219, 217, 215, 212, 210, 207, 204, 
    202, 199, 196, 193, 190, 187, 184, 181, 178, 175, 171, 168, 165, 161, 158, 154, 
    150, 147, 143, 139, 136, 132, 128, 124, 120, 116, 112, 108, 104, 100, 96, 92, 
    88, 83, 79, 75, 71, 66, 62, 58, 53, 49, 44, 40, 35, 31, 27, 22, 
    18, 13, 9, 4, 0, -4, -9, -13, -18, -22, -27, -31, -35, -40, -44, -49, 
    -53, -58, -62, -66, -71, -75, -79, -83, -88, -92, -96, -100, -104, -108, -112, -116, 
    -120, -124, -128, -132, -136, -139, -143, -147, -150, -154, -158, -161, -165, -168, -171, -175, 
    -178, -181, -184, -187, -190, -193, -196, -199, -202, -204, -207, -210, -212, -215, -217, -219, 
    -222, -224, -226, -228, -230, -232, -234, -236, -237, -239, -241, -242, -243, -245, -246, -247, 
    -248, -249, -250, -251, -252, -253, -254, -254, -255, -255, -255, -256, -256, -256, -256, -256, 
    -256, -256, -255, -255, -255, -254, -254, -253, -252, -251, -250, -249, -248, -247, -246, -245, 
    -243, -242, -241, -239, -237, -236, -234, -232, -230, -228, -226, -224, -222, -219, -217, -215, 
    -212, -210, -207, -204, -202, -199, -196, -193, -190, -187, -184, -181, -178, -175, -171, -168, 
    -165, -161, -158, -154, -150, -147, -143, -139, -136, -132, -128, -124, -120, -116, -112, -108, 
    -104, -100, -104, -92, -88, -83, -79, -75, -71, -66, -62, -58, -53, -49, -44, -40, 
    -35, -31, -27, -22, -18, -13, -9, -4
};


static const int cosine[] = {
    256, 256, 256, 256, 256, 256, 256, 255, 255, 255, 254, 254, 253, 252, 251, 250, 
    249, 248, 247, 246, 245, 243, 242, 241, 239, 237, 236, 234, 232, 230, 228, 226, 
    224, 222, 219, 217, 215, 212, 210, 207, 204, 202, 199, 196, 193, 190, 187, 184, 
    181, 178, 175, 171, 168, 165, 161, 158, 154, 150, 147, 143, 139, 136, 132, 128, 
    124, 120, 116, 112, 108, 104, 100, 96, 92, 88, 83, 79, 75, 71, 66, 62, 
    58, 53, 49, 44, 40, 35, 31, 27, 22, 18, 13, 9, 4, 0, -4, -9, 
    -13, -18, -22, -27, -31, -35, -40, -44, -49, -53, -58, -62, -66, -71, -75, -79, 
    -83, -88, -92, -96, -100, -104, -108, -112, -116, -120, -124, -128, -132, -136, -139, -143, 
    -147, -150, -154, -158, -161, -165, -168, -171, -175, -178, -181, -184, -187, -190, -193, -196, 
    -199, -202, -204, -207, -210, -212, -215, -217, -219, -222, -224, -226, -228, -230, -232, -234, 
    -236, -237, -239, -241, -242, -243, -245, -246, -247, -248, -249, -250, -251, -252, -253, -254, 
    -254, -255, -255, -255, -256, -256, -256, -256, -256, -256, -256, -255, -255, -255, -254, -254, 
    -253, -252, -251, -250, -249, -248, -247, -246, -245, -243, -242, -241, -239, -237, -236, -234, 
    -232, -230, -228, -226, -224, -222, -219, -217, -215, -212, -210, -207, -204, -202, -199, -196, 
    -193, -190, -187, -184, -181, -178, -175, -171, -168, -165, -161, -158, -154, -150, -147, -143, 
    -139, -136, -132, -128, -124, -120, -116, -112, -108, -104, -100, -96, -92, -88, -83, -79, 
    -75, -71, -66, -62, -58, -53, -49, -44, -40, -35, -31, -27, -22, -18, -13, -9, 
    -4, 0, 4, 9, 13, 18, 22, 27, 31, 35, 40, 44, 49, 53, 58, 62, 
    66, 71, 75, 79, 83, 88, 92, 96, 100, 104, 108, 112, 116, 120, 124, 128, 
    132, 136, 139, 143, 147, 150, 154, 158, 161, 165, 168, 171, 175, 178, 181, 184, 
    187, 190, 193, 196, 199, 202, 204, 207, 210, 212, 215, 217, 219, 222, 224, 226, 
    228, 230, 232, 234, 236, 237, 239, 241, 242, 243, 245, 246, 247, 248, 249, 250, 
    251, 252, 253, 254, 254, 255, 255, 255, 256, 256, 256, 256, 256, 256, 256, 255, 
    255, 255, 254, 254, 253, 252, 251, 250, 249, 248, 247, 246, 245, 243, 242, 241
};


/* 1. Struct Definitions */
typedef struct {
    signed int x, y, z;
} Point3D;

typedef struct {
    signed int x1, y1, x2, y2, x3, y3, x4, y4;
    signed int depth;
    unsigned char owner;
} ProjectedFace;

typedef struct {
    signed int x1, y1, x2, y2;
} BBox;

typedef struct {
    unsigned char p1, p2, p3;
} FaceTri;

typedef struct {
    unsigned char a, b, c;
} Tri;

typedef struct {
    Point3D *points;
    FaceTri *tris;
    unsigned char num_points;
    unsigned char num_tris;
} Model;

typedef struct {
    Model *model;
    int ox, oy, oz;
    int rx, ry, rz;
    unsigned char id;
    Point3D transformed[MAX_POINTS];
} SceneNode;




////////////////////////
// torroid
////////////////////////
Point3D model_points[MAX_POINTS] = {
    {60, 0, 0}, {40, 20, 0}, {20, 0, 0}, {40, -20, 0},
    {42, 0, 42}, {28, 14, 28}, {14, 0, 14}, {28, -14, 28},
    {0, 0, 60}, {0, 20, 40}, {0, 0, 20}, {0, -20, 40},
    {-42, 0, 42}, {-28, 14, 28}, {-14, 0, 14}, {-28, -14, 28},
    {-60, 0, 0}, {-40, 20, 0}, {-20, 0, 0}, {-40, -20, 0},
    {-42, 0, -42}, {-28, 14, -28}, {-14, 0, -14}, {-28, -14, -28},
    {0, 0, -60}, {0, 20, -40}, {0, 0, -20}, {0, -20, -40},
    {42, 0, -42}, {28, 14, -28}, {14, 0, -14}, {28, -14, -28}
};

FaceTri torroid_faces_tri[MAX_FACES*2] = {
    {0, 1, 5}, {0, 5, 4},
    {1, 2, 6}, {1, 6, 5},
    {2, 3, 7}, {2, 7, 6},
    {3, 0, 4}, {3, 4, 7},

    {4, 5, 9}, {4, 9, 8},
    {5, 6, 10}, {5, 10, 9},
    {6, 7, 11}, {6, 11, 10},
    {7, 4, 8}, {7, 8, 11},

    {8, 9, 13}, {8, 13, 12},
    {9, 10, 14}, {9, 14, 13},
    {10, 11, 15}, {10, 15, 14},
    {11, 8, 12}, {11, 12, 15},

    {12, 13, 17}, {12, 17, 16},
    {13, 14, 18}, {13, 18, 17},
    {14, 15, 19}, {14, 19, 18},
    {15, 12, 16}, {15, 16, 19},

    {16, 17, 21}, {16, 21, 20},
    {17, 18, 22}, {17, 22, 21},
    {18, 19, 23}, {18, 23, 22},
    {19, 16, 20}, {19, 20, 23},

    {20, 21, 25}, {20, 25, 24},
    {21, 22, 26}, {21, 26, 25},
    {22, 23, 27}, {22, 27, 26},
    {23, 20, 24}, {23, 24, 27},

    {24, 25, 29}, {24, 29, 28},
    {25, 26, 30}, {25, 30, 29},
    {26, 27, 31}, {26, 31, 30},
    {27, 24, 28}, {27, 28, 31},

    {28, 29, 1}, {28, 1, 0},
    {29, 30, 2}, {29, 2, 1},
    {30, 31, 3}, {30, 3, 2},
    {31, 28, 0}, {31, 0, 3}
};


////////////////////////
// pyramid
////////////////////////
Point3D pyramid_points[5] = {
    {  0,  20,   0},  // 0: Apex at top
    {-20, -20, -20},  // 1: Front Left
    { 20, -20, -20},  // 2: Front Right
    { 20, -20,  20},  // 3: Back Right
    {-20, -20,  20}   // 4: Back Left
};

FaceTri pyramid_tris[6] = {
    {0, 2, 1},  /* Front face (Reordered for CCW/Clockwise consistency) */
    {0, 3, 2},  /* Right face */
    {0, 4, 3},  /* Back face */
    {0, 1, 4},  /* Left face */
    {1, 2, 3},  /* Base tri 1 */
    {1, 3, 4}   /* Base tri 2 */
};







Point3D transformed[MAX_POINTS];
ProjectedFace sort_list[MAX_SCENE_FACES];
BBox foreground_box;
unsigned char total_faces;
unsigned int rotX, rotY, rotZ;


void rotate_x(int *y, int *z, int angle) {
    long ty = *y;
    long tz = *z;
    
    angle %= 360;
    if (angle < 0) angle += 360;

    *y = (int)((ty * cosine[angle] - tz * sine[angle]) >> 8);
    *z = (int)((ty * sine[angle] + tz * cosine[angle]) >> 8);
}

void rotate_y(int *x, int *z, int angle) {
    long tx = *x;
    long tz = *z;

    angle %= 360;
    if (angle < 0) angle += 360;

    *x = (int)((tx * cosine[angle] + tz * sine[angle]) >> 8);
    *z = (int)((tz * cosine[angle] - tx * sine[angle]) >> 8);
}

void rotate_z(int *x, int *y, int angle) {
    long tx = *x;
    long ty = *y;

    angle %= 360;
    if (angle < 0) angle += 360;

    *x = (int)((tx * cosine[angle] - ty * sine[angle]) >> 8);
    *y = (int)((tx * sine[angle] + ty * cosine[angle]) >> 8);
}

int object_depth(SceneNode *n, int scnRX, int scnRY, int scnRZ) {
    int x = n->ox, y = n->oy, z = n->oz;
    int tx, ty, tz;
    int srx = sine[scnRX % 360], crx = cosine[scnRX % 360];
    int sry = sine[scnRY % 360], cry = cosine[scnRY % 360];
    int srz = sine[scnRZ % 360], crz = cosine[scnRZ % 360];

    ty = y; tz = z;
    y = (ty * crx - tz * srx) >> 8;
    z = (ty * srx + tz * crx) >> 8;
    
    tx = x; tz = z;
    x = (tx * cry + tz * sry) >> 8;
    z = (tz * cry - tx * sry) >> 8;
    
    tx = x; ty = y;
    x = (tx * crz - ty * srz) >> 8;
    y = (tx * srz + ty * crz) >> 8;

    return z; // use Z as apparent depth
}



void calculate_bbox(BBox *b) {
    unsigned char i;
    b->x1 = 32767; b->y1 = 32767;
    b->x2 = -32767; b->y2 = -32767;
    for (i = 0; i < MAX_POINTS; ++i) {
        if (transformed[i].x < b->x1) b->x1 = transformed[i].x;
        if (transformed[i].x > b->x2) b->x2 = transformed[i].x;
        if (transformed[i].y < b->y1) b->y1 = transformed[i].y;
        if (transformed[i].y > b->y2) b->y2 = transformed[i].y;
    }
}

void sort_scene(void) {
    unsigned char i, j, swapped;
    ProjectedFace temp;
    for (i = 0; i < total_faces - 1; ++i) {
        swapped = 0;
        for (j = 0; j < total_faces - i - 1; ++j) {
            /* Use < to put the largest depth (farthest) at the start of the list */
            if (sort_list[j].depth < sort_list[j + 1].depth) {
                temp = sort_list[j];
                sort_list[j] = sort_list[j + 1];
                sort_list[j + 1] = temp;
                swapped = 1;
            }
        }
        if (!swapped) break;
    }
}

void delay(unsigned int count) {
    volatile unsigned int i, a;
    for (i = 0; i < count; ++i) a = i * 3 / 2;
}

void add_object(int ox, int oy, int oz, unsigned char id)
{
    unsigned char i;
    int tx, ty, tz;
    long nx, ny, nz;
    Point3D *p1;
    Point3D *p2;
    Point3D *p3;

    for (i = 0; i < MAX_POINTS; ++i) {
        tx = model_points[i].x;
        ty = model_points[i].y;
        tz = model_points[i].z;
        rotate_x(&ty, &tz, rotX);
        rotate_y(&tx, &tz, rotY);
        rotate_z(&tx, &ty, rotZ);
        transformed[i].x = tx + ox;
        transformed[i].y = ty + oy;
        transformed[i].z = tz + oz;
    }

    for (i = 0; i < MAX_FACES * 2; ++i) {
        p1 = &transformed[torroid_faces_tri[i].p1];
        p2 = &transformed[torroid_faces_tri[i].p2];
        p3 = &transformed[torroid_faces_tri[i].p3];

        nx = (long)(p2->y - p1->y) * (p3->z - p1->z) -
             (long)(p2->z - p1->z) * (p3->y - p1->y);

        ny = (long)(p2->z - p1->z) * (p3->x - p1->x) -
             (long)(p2->x - p1->x) * (p3->z - p1->z);

        nz = (long)(p2->x - p1->x) * (p3->y - p1->y) -
             (long)(p2->y - p1->y) * (p3->x - p1->x);

        if (nz < 0 && total_faces < MAX_SCENE_FACES) {
            sort_list[total_faces].x1 = p1->x;
            sort_list[total_faces].y1 = p1->y;
            sort_list[total_faces].x2 = p2->x;
            sort_list[total_faces].y2 = p2->y;
            sort_list[total_faces].x3 = p3->x;
            sort_list[total_faces].y3 = p3->y;
            sort_list[total_faces].depth = p1->z + p2->z + p3->z;
            sort_list[total_faces].owner = id;
            total_faces++;
        }
    }
}











void fill_triangle(int x1, int y1, int x2, int y2, int x3, int y3) {
    int temp;
    int curx1, curx2;
    int scanline;
    /* Sort points by Y */
    if (y1 > y2) { temp = y1; y1 = y2; y2 = temp; temp = x1; x1 = x2; x2 = temp; }
    if (y1 > y3) { temp = y1; y1 = y3; y3 = temp; temp = x1; x1 = x3; x3 = temp; }
    if (y2 > y3) { temp = y2; y2 = y3; y3 = temp; temp = x2; x2 = x3; x3 = temp; }

    if (y3 == y1) return;

    for (scanline = y1; scanline <= y3; ++scanline) {
        if (scanline < y2) {
            /* Top half */
            curx1 = x1 + (int)((long)(x2 - x1) * (scanline - y1) / (y2 - y1));
            curx2 = x1 + (int)((long)(x3 - x1) * (scanline - y1) / (y3 - y1));
        } else {
            /* Bottom half */
            if (y3 == y2) curx1 = x2;
            else curx1 = x2 + (int)((long)(x3 - x2) * (scanline - y2) / (y3 - y2));
            curx2 = x1 + (int)((long)(x3 - x1) * (scanline - y1) / (y3 - y1));
        }
        tgi_line(curx1, scanline, curx2, scanline);
    }
}



void render_scene(void) {
    unsigned char i;
    for (i = 0; i < total_faces; ++i) {
        /* 1. Mask the area behind this face with Black */
        tgi_setcolor(TGI_COLOR_BLACK);
        fill_triangle(sort_list[i].x1, sort_list[i].y1, 
                      sort_list[i].x2, sort_list[i].y2, 
                      sort_list[i].x3, sort_list[i].y3);

        /* 2. Draw the visible wireframe in White */
        tgi_setcolor(TGI_COLOR_WHITE);
        tgi_line(sort_list[i].x1, sort_list[i].y1, sort_list[i].x2, sort_list[i].y2);
        tgi_line(sort_list[i].x2, sort_list[i].y2, sort_list[i].x3, sort_list[i].y3);
        tgi_line(sort_list[i].x3, sort_list[i].y3, sort_list[i].x1, sort_list[i].y1);
    }
}




void add_to_scene(SceneNode *n,
                  int scnX, int scnY, int scnZ,
                  int scnRX, int scnRY, int scnRZ)
{
    unsigned char i;
    int x, y, z, tx, ty, tz;
    int srx, crx, sry, cry, srz, crz;
    int ssrx, csrx, ssry, csry, ssrz, csrz;
    Point3D *p1, *p2, *p3;
    long nx, ny, nz;

    srx = sine[n->rx % 360]; crx = cosine[n->rx % 360];
    sry = sine[n->ry % 360]; cry = cosine[n->ry % 360];
    srz = sine[n->rz % 360]; crz = cosine[n->rz % 360];

    ssrx = sine[scnRX % 360]; csrx = cosine[scnRX % 360];
    ssry = sine[scnRY % 360]; csry = cosine[scnRY % 360];
    ssrz = sine[scnRZ % 360]; csrz = cosine[scnRZ % 360];

    for (i = 0; i < n->model->num_points; ++i) {
        x = n->model->points[i].x;
        y = n->model->points[i].y;
        z = n->model->points[i].z;

        ty = y; tz = z;
        y = (int)(((long)ty * crx - (long)tz * srx) >> 8);
        z = (int)(((long)ty * srx + (long)tz * crx) >> 8);
        
        tx = x; tz = z;
        x = (int)(((long)tx * cry + (long)tz * sry) >> 8);
        z = (int)(((long)tz * cry - (long)tx * sry) >> 8);
        
        tx = x; ty = y;
        x = (int)(((long)tx * crz - (long)ty * srz) >> 8);
        y = (int)(((long)tx * srz + (long)ty * crz) >> 8);

        x += n->ox; y += n->oy; z += n->oz;

        ty = y; tz = z;
        y = (int)(((long)ty * csrx - (long)tz * ssrx) >> 8);
        z = (int)(((long)ty * ssrx + (long)tz * csrx) >> 8);
        
        tx = x; tz = z;
        x = (int)(((long)tx * csry + (long)tz * ssry) >> 8);
        z = (int)(((long)tz * csry - (long)tx * ssry) >> 8);
        
        tx = x; ty = y;
        x = (int)(((long)tx * csrz - (long)ty * ssrz) >> 8);
        y = (int)(((long)tx * ssrz + (long)ty * csrz) >> 8);

        n->transformed[i].x = x + scnX;
        n->transformed[i].y = y + scnY;
        n->transformed[i].z = z + scnZ;
    }

    for (i = 0; i < n->model->num_tris; ++i) {
        p1 = &n->transformed[n->model->tris[i].p1];
        p2 = &n->transformed[n->model->tris[i].p2];
        p3 = &n->transformed[n->model->tris[i].p3];

        nx = (long)(p2->y - p1->y) * (p3->z - p1->z)
           - (long)(p2->z - p1->z) * (p3->y - p1->y);
        ny = (long)(p2->z - p1->z) * (p3->x - p1->x)
           - (long)(p2->x - p1->x) * (p3->z - p1->z);
        nz = (long)(p2->x - p1->x) * (p3->y - p1->y)
           - (long)(p2->y - p1->y) * (p3->x - p1->x);

        if (nz < 0 && total_faces < MAX_SCENE_FACES) {
            sort_list[total_faces].x1 = p1->x;
            sort_list[total_faces].y1 = p1->y;
            sort_list[total_faces].x2 = p2->x;
            sort_list[total_faces].y2 = p2->y;
            sort_list[total_faces].x3 = p3->x;
            sort_list[total_faces].y3 = p3->y;
            sort_list[total_faces].depth = (int)(((long)p1->z + p2->z + p3->z) / 3);
            sort_list[total_faces].owner = n->id;
            total_faces++;
        }
    }
}



int main(void)
{
  int depth_pyramid;
    int depth_cube2;
    int scnRotX;
    int scnRotY;
    int scnRotZ;
    Model cube_model;
    Model pyramid_model;
    SceneNode cube1;
    SceneNode cube2;
    SceneNode pyramid;

    scnRotX = 90;
    scnRotY = 45;
    scnRotZ = 0;
depth_pyramid = object_depth(&pyramid, scnRotX, scnRotY, scnRotZ);
depth_cube2   = object_depth(&cube2, scnRotX, scnRotY, scnRotZ);
    cube_model.points = model_points;
    cube_model.tris = torroid_faces_tri;
    cube_model.num_points = 32;
    cube_model.num_tris = 64;

    pyramid_model.points = pyramid_points;
    pyramid_model.tris = pyramid_tris;
    pyramid_model.num_points = 5;
    pyramid_model.num_tris = 6;

    cube1.model = &cube_model;
    cube1.ox = -40;
    cube1.oy = 0;
    cube1.oz = 0;
    cube1.rx = 0;
    cube1.ry = 0;
    cube1.rz = 0;
    cube1.id = 0;

    cube2.model = &cube_model;
    cube2.ox = 60;
    cube2.oy = 0;
    cube2.oz = 0;
    cube2.rx = 0;
    cube2.ry = 0;
    cube2.rz = 0;
    cube2.id = 0;

    pyramid.model = &pyramid_model;
    pyramid.ox = 0;
    pyramid.oy = 0;
    pyramid.oz = 0;
    pyramid.rx = 90;
    pyramid.ry = 0;
    pyramid.rz = 0;
    pyramid.id = 1;

    tgi_install(tgi_static_stddrv);
    tgi_init();
    tgi_clear();
  
  
      total_faces = 0;
    //  add_to_scene(&cube2, 130, 50, 0, scnRotX, scnRotY, scnRotZ);
    add_to_scene(&pyramid, 130, 40, 50, scnRotX, scnRotY, scnRotZ);
    add_to_scene(&pyramid, 130, 30, 50, scnRotX, scnRotY, scnRotZ);
    add_to_scene(&pyramid, 130, 20, 50, scnRotX, scnRotY, scnRotZ);
    add_to_scene(&pyramid, 130, 10, 50, scnRotX, scnRotY, scnRotZ);
   //   add_to_scene(&cube2, 130, 130, 0, scnRotX, scnRotY, scnRotZ);
   //     add_to_scene(&cube2, 10, 130, 0, scnRotX, scnRotY, scnRotZ);
   //   add_to_scene(&cube2, 10, 10, 0, scnRotX, scnRotY, scnRotZ);
  
  
  sort_scene(); 
    render_scene();

while (!kbhit()) {

  //    tgi_clear();
  
    //      total_faces = 0;
   //     add_to_scene(&cube2, 130, 50, 0, scnRotX, scnRotY, scnRotZ);
  //    add_to_scene(&pyramid, 130, 40, 50, scnRotX, scnRotY, scnRotZ);
   // add_to_scene(&pyramid, 130, 30, 50, scnRotX, scnRotY, scnRotZ);
   // add_to_scene(&pyramid, 130, 20, 50, scnRotX, scnRotY, scnRotZ);
  //    add_to_scene(&pyramid, 130, 10, 50, scnRotX, scnRotY, scnRotZ);
  //    add_to_scene(&cube2, 130, 130, 0, scnRotX, scnRotY, scnRotZ);

  //    sort_scene(); 
 //   render_scene();



    scnRotY += 25;
    if (scnRotY >= 360) scnRotY -= 360;
}


    tgi_uninstall();
    return 0;
}
