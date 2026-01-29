#include <conio.h>
#include <tgi.h>
#include <c64.h>
//#include <mouse.h>
#include <stdio.h>
#include <stdlib.h>
#include <cbm_petscii_charmap.h>
#include "objectloader.h"

#define COLOR_BACK          TGI_COLOR_BLACK
#define COLOR_FORE          TGI_COLOR_WHITE

// external functions
extern const int cosine[];
extern const int sine[];
extern SceneNode *objects[MAX_OBJECTS];
int load_model(const char *filename, unsigned int device, Model *m, Point3D *point_array, FaceTri *tri_array);
int save_model(const char *filename, unsigned int device, Model *m);
int load_object(const char *name, unsigned char device);
void list_disk(unsigned char device);
void objectstateprint(void);
extern int object_count;

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



// int get_owner_at(int mx, int my) {
//     int i;
//     long d1, d2, d3;
//     int has_neg, has_pos;

//     for (i = total_faces - 1; i >= 0; --i) {
//         /* Cross product test for each edge */
//         d1 = (long)(mx - sort_list[i].x2) * (sort_list[i].y1 - sort_list[i].y2) - (long)(sort_list[i].x1 - sort_list[i].x2) * (my - sort_list[i].y2);
//         d2 = (long)(mx - sort_list[i].x3) * (sort_list[i].y2 - sort_list[i].y3) - (long)(sort_list[i].x2 - sort_list[i].x3) * (my - sort_list[i].y3);
//         d3 = (long)(mx - sort_list[i].x1) * (sort_list[i].y3 - sort_list[i].y1) - (long)(sort_list[i].x3 - sort_list[i].x1) * (my - sort_list[i].y1);

//         has_neg = (d1 < 0) || (d2 < 0) || (d3 < 0);
//         has_pos = (d1 > 0) || (d2 > 0) || (d3 > 0);

//         if (!(has_neg && has_pos)) {
//             return sort_list[i].owner;
//         }
//     }
//     return -1;
// }

int main(void){
    int i, n;
    int itx;
    int obj_i;
    int p_idx;
    int t_idx;
    int test_passed = 1;
    unsigned int device;
    int scnRotX = 90;
    int scnRotY = 45;
    int scnRotZ = 0;
    void *memallocptr;
    unsigned size = 20000;
    unsigned count = 0;

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
    // add_to_scene(&torroid, 130, 40, 50, scnRotX, scnRotY, scnRotZ);
    sort_scene();
    render_scene();

    // free static coded buffers by name
    free(pyramid.transformed);
    free(torroid.transformed); /* This was missing */

    
    // pause for anykey. inside TGI, no printf here
    // *(unsigned char*)198 = 0;
    // while (!kbhit()) { }
    tgi_clear();
    tgi_uninstall();
    clrscr();
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


    //list_disk(device);

    p_idx = load_object("PRYM,P,R", device);
    if (p_idx >= 0) {
        printf("PRYM loaded: %d pts %d tris, %uKB free\n",
            objects[p_idx]->model->num_points,
            objects[p_idx]->model->num_tris,
            _heapmemavail);
    }

    p_idx = load_object("TORROID,P,R", device);
    if (p_idx >= 0) {
        printf("loaded: %d pts %d tris, %uKB free\n",
            objects[p_idx]->model->num_points,
            objects[p_idx]->model->num_tris,
            _heapmemavail);
    }

    p_idx = load_object("TORROID,P,R", device);
    if (p_idx >= 0) {
        printf("loaded: %d pts %d tris, %uKB free\n",
            objects[p_idx]->model->num_points,
            objects[p_idx]->model->num_tris,
            _heapmemavail);
    }

    p_idx = load_object("TORROID,P,R", device);
    if (p_idx >= 0) {
        printf("loaded: %d pts %d tris, %uKB free\n",
            objects[p_idx]->model->num_points,
            objects[p_idx]->model->num_tris,
            _heapmemavail);
    }


    // printf("Press key to continue...\n");
    // *(unsigned char*)198 = 0;
    // while (!kbhit()) { }

    // activate tgi
    // tgi_install(tgi_static_stddrv);
    // tgi_init();
    // tgi_clear();


    // render
    total_faces = 0;
    for (obj_i = 0; obj_i < object_count; ++obj_i) {
        objects[obj_i]->ox = 0;
        objects[obj_i]->oy = 0;
        objects[obj_i]->oz = 0;
        objects[obj_i]->rx = 90;
        objects[obj_i]->ry = 0;
        objects[obj_i]->rz = 0;
        add_to_scene(objects[obj_i], 130, 40, 50, scnRotX, scnRotY, scnRotZ);
    }

    printf("SORTSCENE\n");
     sort_scene();
     
     printf("RENDERSCENE\n");
     render_scene();


    // debug for test runner , print if anyting failed
    if (test_passed) {
        printf("TEST PASSED\n");
    } else {
        printf("TEST FAILED\n");
    }

   // printf("Press key to continue...\n");
  //  *(unsigned char*)198 = 0;
  //  while (!kbhit()) { }






    //activate tgi
    // tgi_install(tgi_static_stddrv);
    // tgi_init();
    // tgi_clear();
    itx = 0; 


    n = 10;
    i = 0;
    while (size > 1024) {
    itx += 1;
    tgi_clear();

    for (i = 0; i < n; i++) {
        p_idx = load_object("PRYM,P,R", device);
        if (p_idx >= 0) {
            printf("1loaded: %d pts %d tris, %uKB free\n",
                objects[p_idx]->model->num_points,
                objects[p_idx]->model->num_tris,
                _heapmemavail);
        }

        p_idx = load_object("TORROID,P,R", device);
        if (p_idx >= 0) {
            printf("2loaded: %d pts %d tris, %uKB free\n",
                objects[p_idx]->model->num_points,
                objects[p_idx]->model->num_tris,
                _heapmemavail);
        }
    }



    // mem alloc test before object cleanup
    printf("running 1st alloc");
    size = 20000;
    while (size > 1024) {
            memallocptr = malloc(size);
            if (memallocptr) {
                free(memallocptr);
                break; 
            }
            size -= 1024; // shrink alloc attempt by 1k until succeeds
        }



    objectstateprint();

    //    sort_scene();
    //    render_scene();

    //unload dynamic loaded objects
    for (obj_i = 0; obj_i < object_count; ++obj_i) {
        if (!objects[obj_i]) continue;

        if (objects[obj_i]->transformed) {
            free(objects[obj_i]->transformed);
            objects[obj_i]->transformed = NULL;
        }

        if (objects[obj_i]->model) {
            if (objects[obj_i]->model->points) {
                free(objects[obj_i]->model->points);
                objects[obj_i]->model->points = NULL;
            }
            if (objects[obj_i]->model->tris) {
                free(objects[obj_i]->model->tris);
                objects[obj_i]->model->tris = NULL;
            }
            free(objects[obj_i]->model);
            objects[obj_i]->model = NULL;
        }

        free(objects[obj_i]);
        objects[obj_i] = NULL;
    }

    object_count = 0;
            count++;

    printf("\n\nalloc before clean %u: %u bytes\n", count, size);
    // mem alloc test after object cleanup
    size = 20000;
    while (size > 1024) {
            memallocptr = malloc(size);
            if (memallocptr) {
                free(memallocptr);
                break; 
            }
            size -= 1024; /* Shrink by 1KB */
        }
        printf("alloc after %u: %u bytes\n", count, size);
        

       
 }



    // clear kb buffer, unload tgi, exit
    *(unsigned char*)198 = 0;
    tgi_uninstall();
    printf("Exited\n");
    return 0;
}
