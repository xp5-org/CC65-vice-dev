#include <conio.h>
#include <tgi.h>
#include <c64.h>
#include <mouse.h>
#include <stdio.h>
#include <stdlib.h>
#include <cbm_petscii_charmap.h>
#include "objectloader.h"

#define COLOR_BACK          TGI_COLOR_BLACK
#define COLOR_FORE          TGI_COLOR_WHITE
#define MAX_POINTS          182
#define MAX_FACES           122
#define MAX_SCENE_FACES     184

// external functions
extern const int cosine[];
extern const int sine[];
int load_model(const char *filename, unsigned int device, Model *m, Point3D *point_array, FaceTri *tri_array);
int save_model(const char *filename, unsigned int device, Model *m);

// local to main.c
Point3D transformed[MAX_POINTS];
ProjectedFace sort_list[MAX_SCENE_FACES];
BBox foreground_box;
unsigned char total_faces;
unsigned int rotX, rotY, rotZ;


// torroid
Point3D torroid_points[MAX_POINTS] = {
    {60, 0, 0}, {40, 20, 0}, {20, 0, 0}, {40, -20, 0},
    {42, 0, 42}, {28, 14, 28}, {14, 0, 14}, {28, -14, 28},
    {0, 0, 60}, {0, 20, 40}, {0, 0, 20}, {0, -20, 40},
    {-42, 0, 42}, {-28, 14, 28}, {-14, 0, 14}, {-28, -14, 28},
    {-60, 0, 0}, {-40, 20, 0}, {-20, 0, 0}, {-40, -20, 0},
    {-42, 0, -42}, {-28, 14, -28}, {-14, 0, -14}, {-28, -14, -28},
    {0, 0, -60}, {0, 20, -40}, {0, 0, -20}, {0, -20, -40},
    {42, 0, -42}, {28, 14, -28}, {14, 0, -14}, {28, -14, -28}
};


FaceTri torroid_faces_tri[MAX_FACES] = {
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


// pyramid
Point3D pyramid_points[5] = {
    {  0,  20,   0},  //apex at top
    {-20, -20, -20},  //front left
    { 20, -20, -20},  //front right
    { 20, -20,  20},  //back right
    {-20, -20,  20}   //back left
};


FaceTri pyramid_tris[6] = {
    {0, 2, 1},  //frontface
    {0, 3, 2},  //rightface
    {0, 4, 3},  //backface
    {0, 1, 4},  //leftface
    {1, 2, 3},  //base triangle 1
    {1, 3, 4}   //base triangle 2
};


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


void add_object(int ox, int oy, int oz, unsigned char id){
    unsigned char i;
    int tx, ty, tz;
    long nx, ny, nz;
    Point3D *p1;
    Point3D *p2;
    Point3D *p3;

    for (i = 0; i < MAX_POINTS; ++i) {
        tx = torroid_points[i].x;
        ty = torroid_points[i].y;
        tz = torroid_points[i].z;
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
    // sort by Y index
    if (y1 > y2) { temp = y1; y1 = y2; y2 = temp; temp = x1; x1 = x2; x2 = temp; }
    if (y1 > y3) { temp = y1; y1 = y3; y3 = temp; temp = x1; x1 = x3; x3 = temp; }
    if (y2 > y3) { temp = y2; y2 = y3; y3 = temp; temp = x2; x2 = x3; x3 = temp; }

    if (y3 == y1) return;

    for (scanline = y1; scanline <= y3; ++scanline) {
        if (scanline < y2) {
            // top
            curx1 = x1 + (int)((long)(x2 - x1) * (scanline - y1) / (y2 - y1));
            curx2 = x1 + (int)((long)(x3 - x1) * (scanline - y1) / (y3 - y1));
        } else {
            // bottom
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
        // set bg mask
        tgi_setcolor(TGI_COLOR_BLACK);
        fill_triangle(sort_list[i].x1, sort_list[i].y1, 
                      sort_list[i].x2, sort_list[i].y2, 
                      sort_list[i].x3, sort_list[i].y3);

        // draw visible
        tgi_setcolor(TGI_COLOR_WHITE);
        tgi_line(sort_list[i].x1, sort_list[i].y1, sort_list[i].x2, sort_list[i].y2);
        tgi_line(sort_list[i].x2, sort_list[i].y2, sort_list[i].x3, sort_list[i].y3);
        tgi_line(sort_list[i].x3, sort_list[i].y3, sort_list[i].x1, sort_list[i].y1);
    }
}


void add_to_scene(SceneNode *n, int scnX, int scnY, int scnZ, int scnRX, int scnRY, int scnRZ){
    unsigned char i;
    static int x, y, z, tx, ty, tz;
    static int srx, crx, sry, cry, srz, crz;
    static int ssrx, csrx, ssry, csry, ssrz, csrz;
    static Point3D *p1, *p2, *p3;
    static long nx, ny, nz;

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


int main(void){
    int test_passed = 1;
    unsigned int device;
    int scnRotX = 90;
    int scnRotY = 45;
    int scnRotZ = 0;

    // set up transformed points buffer
    Point3D *torroid_trans = NULL;
    Point3D *pyramid_trans = NULL;
    Point3D *loadedpyramid_trans = NULL;
    Point3D *loadedtorroid_trans = NULL;

    // instance new model & scene objects
    Model torroid_model;
    Model pyramid_model;
    SceneNode torroid;
    SceneNode pyramid;

    // vars for load-pyramid test
    SceneNode loadedpyramid;
    Point3D loadedpyramid_points[MAX_POINTS];
    FaceTri loadedpyramid_tris[MAX_FACES];
    Model loadedpyramid_model;

    // vars for load-torroid test
    SceneNode loadedtorroid;
    Point3D loadedtorroid_points[MAX_POINTS];
    FaceTri loadedtorroid_tris[MAX_FACES];
    Model loadedtorroid_model;

    // models init
    torroid_model.points = torroid_points;
    torroid_model.tris = torroid_faces_tri;
    torroid_model.num_points = 32;
    torroid_model.num_tris = 64;

    pyramid_model.points = pyramid_points;
    pyramid_model.tris = pyramid_tris;
    pyramid_model.num_points = 5;
    pyramid_model.num_tris = 6;

    // scene nodes init
    torroid.model = &torroid_model;
    torroid.ox = -40; torroid.oy = 0; torroid.oz = 0;
    torroid.rx = 0; torroid.ry = 0; torroid.rz = 0;
    torroid.id = 0;
    torroid.transformed = torroid_trans;

    pyramid.model = &pyramid_model;
    pyramid.ox = 0; pyramid.oy = 0; pyramid.oz = 0;
    pyramid.rx = 90; pyramid.ry = 0; pyramid.rz = 0;
    pyramid.id = 1;

    // alloc mem for the models transform buffer
    pyramid_trans = malloc(sizeof(Point3D) * pyramid_model.num_points);
    if (!pyramid_trans) {
        printf("Out of memory for pyramid\n");
        return 1;
    }
    pyramid.transformed = pyramid_trans;

    torroid_trans = malloc(sizeof(Point3D) * torroid_model.num_points);
    if (!torroid_trans) {
        printf("Out of memory for torroid\n");
        return 1;
    }
    torroid.transformed = torroid_trans;


    // init tgi
    tgi_install(tgi_static_stddrv);
    tgi_init();
    tgi_clear();

    // add built-in objs to scene. depth-sort & render
    total_faces = 0;
    add_to_scene(&pyramid, 130, 40, 50, scnRotX, scnRotY, scnRotZ);
    add_to_scene(&torroid, 130, 40, 50, scnRotX, scnRotY, scnRotZ);
    sort_scene();
    render_scene();



    
    // pause for anykey. inside TGI, no printf here
    *(unsigned char*)198 = 0;
    while (!kbhit()) { }
    tgi_clear();
    tgi_uninstall();
    printf("Beginning save test\n");




    // write demo objs to disk
    device = 8;
    if (save_model("PRYM,P,W", device, &pyramid_model)) {
        printf("SUCCESS: Pyramid model saved.\n");
    } else {
        printf("Failed to save pyramid model.\n");
        test_passed = 0;
    }

    if (save_model("TORROID,P,W", device, &torroid_model)) {
        printf("SUCCESS: torroid model saved.\n");
    } else {
        printf("Failed to save torroid model.\n");
        test_passed = 0;
    }


    // load pyramid_model from disk
    if (load_model("PRYM,P,R", device, &loadedpyramid_model, loadedpyramid_points, loadedpyramid_tris)) {
        printf("SUCCESS: Pyramid model loaded. Points: %d, Tris: %d\n",
               loadedpyramid_model.num_points, loadedpyramid_model.num_tris);

        loadedpyramid.model = &loadedpyramid_model;
        loadedpyramid.transformed = malloc(sizeof(Point3D) * loadedpyramid_model.num_points);
        if (!loadedpyramid.transformed) {
            printf("Out of memory for loaded pyramid\n");
            free(pyramid.transformed);
            return 1;
        }
    
        // debug - print heapmem
        printf("heapmemavai: %u\n", _heapmemavail());
    } else {
        printf("Failed to load pyramid model.\n");
        test_passed = 0;
    }


    // load back the models
    if (load_model("TORROID,P,R", device, &loadedtorroid_model, loadedtorroid_points, loadedtorroid_tris)) {
        printf("SUCCESS: Pyramid model loaded. Points: %d, Tris: %d\n",
               loadedtorroid_model.num_points, loadedtorroid_model.num_tris);

        loadedtorroid.model = &loadedtorroid_model;
        loadedtorroid.transformed = malloc(sizeof(Point3D) * loadedtorroid_model.num_points);
        if (!loadedtorroid.transformed) {
            printf("Out of memory for loaded torroid\n");
            free(torroid.transformed);
            return 1;
        }

        // debug - print heapmem
        printf("heapmemavai: %u\n", _heapmemavail());
    } else {
        printf("Failed to load pyramid model.\n");
        test_passed = 0;
    }





    // pause for anykey
    *(unsigned char*)198 = 0;
    printf("load complete, press any key to render loaded objects\n");
    while (!kbhit()) { }


    // activate tgi
    tgi_install(tgi_static_stddrv);
    tgi_init();
    tgi_clear();


    //scene setup
    loadedtorroid.ox = 0; loadedtorroid.oy = 0; loadedtorroid.oz = 0;
    loadedtorroid.rx = 90; loadedtorroid.ry = 0; loadedtorroid.rz = 0;
    loadedtorroid.id = 1;

    loadedpyramid.ox = 0; loadedpyramid.oy = 0; loadedpyramid.oz = 0;
    loadedpyramid.rx = 90; loadedpyramid.ry = 0; loadedpyramid.rz = 0;
    loadedpyramid.id = 1;


    // render
    total_faces = 0;
    add_to_scene(&loadedtorroid, 130, 40, 50, scnRotX, scnRotY, scnRotZ);
    add_to_scene(&loadedpyramid, 130, 40, 50, scnRotX, scnRotY, scnRotZ);
    sort_scene();
    render_scene();


    // debug for test runner , print if anyting failed
    if (test_passed) {
        printf("TEST PASSED\n");
    } else {
        printf("TEST FAILED\n");
    }

    printf("Press key to continue...\n");
    *(unsigned char*)198 = 0;
    while (!kbhit()) { }



    // free buffers by name
    free(pyramid.transformed);
    if (loadedpyramid.transformed) {
        free(loadedpyramid.transformed);
        free(loadedtorroid.transformed);
    }


    // clear kb buffer, unload tgi, exit
    *(unsigned char*)198 = 0;
    tgi_uninstall();
    return 0;
}
