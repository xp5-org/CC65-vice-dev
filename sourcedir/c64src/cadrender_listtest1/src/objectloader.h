#ifndef MODEL_DEFS_H
#define MODEL_DEFS_H

#define MAX_POINTS      48
#define MAX_FACES       64
#define MAX_SCENE_FACES 484
#define MAX_OBJECTS 64
#define MAX_BUF 1024

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
    Point3D *points;
    FaceTri *tris;
    unsigned char num_points;
    unsigned char num_tris;
} Model;

typedef struct {
    Model *model;
    Point3D *transformed;
    int ox, oy, oz;
    int rx, ry, rz;
    unsigned char id;
} SceneNode;

#endif
