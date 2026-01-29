#include <cbm.h>
#include <stdio.h>
#include <stdlib.h>
#include <conio.h>
#include <string.h>
#include "objectloader.h"

#define MAX_BUF 1024
static unsigned char file_buffer[MAX_BUF];
#define MAX_OBJECTS 64
SceneNode *objects[MAX_OBJECTS];
int object_count = 0;


int save_model(const char *filename, unsigned int device, Model *m){
    unsigned char *ptr = file_buffer;
    unsigned int channel = 1;
    unsigned int i;

    if (!m || !m->points || !m->tris) return 0;

    *ptr++ = 0x00;
    *ptr++ = 0x00;
    *ptr++ = m->num_points;
    *ptr++ = m->num_tris;

    for (i = 0; i < m->num_points; i++) {
        *ptr++ = (unsigned char)(m->points[i].x & 0xFF);
        *ptr++ = (unsigned char)((m->points[i].x >> 8) & 0xFF);
        *ptr++ = (unsigned char)(m->points[i].y & 0xFF);
        *ptr++ = (unsigned char)((m->points[i].y >> 8) & 0xFF);
        *ptr++ = (unsigned char)(m->points[i].z & 0xFF);
        *ptr++ = (unsigned char)((m->points[i].z >> 8) & 0xFF);
    }

    for (i = 0; i < m->num_tris; i++) {
        *ptr++ = m->tris[i].p1;
        *ptr++ = m->tris[i].p2;
        *ptr++ = m->tris[i].p3;
    }

    if (cbm_open(channel, device, channel, filename) != 0) return 0;
    if (cbm_write(channel, file_buffer, (int)(ptr - file_buffer)) != (int)(ptr - file_buffer)) {
        cbm_close(channel);
        return 0;
    }
    cbm_close(channel);
    return 1;
}


void parse_model_data(unsigned char *ptr, Model *m){
    int i;
    for (i = 0; i < m->num_points; i++) {
        m->points[i].x = ptr[0] | (ptr[1] << 8); ptr += 2;
        m->points[i].y = ptr[0] | (ptr[1] << 8); ptr += 2;
        m->points[i].z = ptr[0] | (ptr[1] << 8); ptr += 2;
    }
    for (i = 0; i < m->num_tris; i++) {
        m->tris[i].p1 = *ptr++;
        m->tris[i].p2 = *ptr++;
        m->tris[i].p3 = *ptr++;
    }
}


int load_object(const char *name, unsigned char device){
    Model *m;
    SceneNode *n;
    unsigned int channel = 2;
    int bytes_read;

    if (object_count >= MAX_OBJECTS) return -1;

    if (cbm_open(channel, device, channel, name) != 0) return -1;
    
    /* Read header to get counts: 2 byte PRG addr + num_pts + num_tris */
    bytes_read = cbm_read(channel, file_buffer, 4);
    if (bytes_read < 4) {
        cbm_close(channel);
        return -1;
    }

    m = malloc(sizeof(Model));
    if (!m) { cbm_close(channel); return -1; }

    m->num_points = file_buffer[2];
    m->num_tris   = file_buffer[3];

    m->points = malloc(sizeof(Point3D) * m->num_points);
    m->tris   = malloc(sizeof(FaceTri) * m->num_tris);

    if (!m->points || !m->tris) {
        if (m->points) free(m->points);
        if (m->tris) free(m->tris);
        free(m);
        cbm_close(channel);
        return -1;
    }

    bytes_read = cbm_read(channel, file_buffer, MAX_BUF);
    cbm_close(channel);

    parse_model_data(file_buffer, m);

    n = malloc(sizeof(SceneNode));
    if (!n) {
        free(m->points); free(m->tris); free(m);
        return -1;
    }

    n->transformed = malloc(sizeof(Point3D) * m->num_points);
    if (!n->transformed) {
        free(n); free(m->points); free(m->tris); free(m);
        return -1;
    }

    n->model = m;
    n->ox = n->oy = n->oz = 0;
    n->rx = n->ry = n->rz = 0;
    n->id = object_count;

    objects[object_count++] = n;
    return object_count - 1;
}


void objectstateprint(void){
    unsigned int total_mem = 0;
    unsigned int i, mem = 0;
    printf("Object list:\n");
    printf("ID  | Points | Tris | bytes\n");
    printf("----------------------------------------\n");

    for (i = 0; i < object_count; ++i) {
        if (!objects[i]) continue;
        mem = 0;
        mem += sizeof(SceneNode);

        if (objects[i]->transformed) {
            mem += sizeof(Point3D) * objects[i]->model->num_points;
        }

        if (objects[i]->model) {
            mem += sizeof(Model);
            if (objects[i]->model->points) mem += sizeof(Point3D) * objects[i]->model->num_points;
            if (objects[i]->model->tris)   mem += sizeof(FaceTri) * objects[i]->model->num_tris;
        }

        total_mem += mem;

        printf("%3d | %6d | %5d | %10u\n",
               objects[i]->id,
               objects[i]->model->num_points,
               objects[i]->model->num_tris,
               mem);
    }

    printf("Total memory used by all objects: %u bytes\n", total_mem);
}





// void list_disk(unsigned char device) {
//     unsigned char buffer[32];
//     unsigned int read;
    
//     /* Open directory for reading */
//     if (cbm_open(2, device, 2, "$") != 0) {
//         printf("Error opening dir\n");
//         return;
//     }

//     /* Skip the load address (2 bytes) and disk header (approx 28-30 bytes) */
//     /* C64 dir lines: [LinkL][LinkH][SizeL][SizeH][Quotes][Name][Quotes]... */
//     cbm_read(2, buffer, 32); 

//     while (1) {
//         /* Read next line: 2 bytes link pointer, 2 bytes file size */
//         if (cbm_read(2, buffer, 4) < 4) break;
        
//         /* The C64 directory stores size in blocks (254 bytes each) */
//         read = buffer[2] | (buffer[3] << 8);

//         /* Read the line content until the end of the filename area */
//         /* Typically filenames start with a quote and are 16 chars long */
//         if (cbm_read(2, buffer, 28) < 28) break;

//         /* Print the line if size > 0 (skips 'blocks free' usually) */
//         /* This is a raw dump of the line; you may need to parse quotes */
//         printf("%u %s\n", read, buffer);
//     }

//     cbm_close(2);
// }