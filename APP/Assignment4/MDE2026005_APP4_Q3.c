/*
Take a 3-dimensional array, say a[p][r][c], where p denotes planes, each with r rows and 
c columns. Initialize the array with numbers sequentially from 1 to p*r*c, and take a 
pointer, x, pointing to the base address of the array. Write a C program to print the 
maximum  element  among  the  corner elements of each plane accessed through the 
pointer. (refer Q2 in Lab 2 assignment).
*/

#include <stdio.h>

#define P 2
#define R 3
#define C 4

int main(void) {
    int a[P][R][C];
    int *x;
    int count = 1;

    // Initialize array sequentially from 1 to p*r*c 
    for (int i = 0; i < P; i++)
        for (int j = 0; j < R; j++)
            for (int k = 0; k < C; k++)
                a[i][j][k] = count++;

    printf("Array elements:\n");
    for (int i = 0; i < P; i++) {
        printf("Plane %d:\n", i);
        for (int j = 0; j < R; j++) {
            for (int k = 0; k < C; k++) {
                printf("%4d", a[i][j][k]);
            }
            printf("\n");
        }
    }

    x = &a[0][0][0];

    // For each plane, find the max among its 4 corner elements 
    printf("\nMaximum corner element of each plane:\n");
    for (int i = 0; i < P; i++) {
        int planeBase = i * R * C;

        int topLeft     = *(x + planeBase + 0 * C + 0);
        int topRight    = *(x + planeBase + 0 * C + (C - 1));
        int bottomLeft  = *(x + planeBase + (R - 1) * C + 0);
        int bottomRight = *(x + planeBase + (R - 1) * C + (C - 1));

        int max = topLeft;
        if (topRight > max)    max = topRight;
        if (bottomLeft > max)  max = bottomLeft;
        if (bottomRight > max) max = bottomRight;

        printf("Plane %d: corners = %d, %d, %d, %d -> max = %d\n",
               i, topLeft, topRight, bottomLeft, bottomRight, max);
    }

    return 0;
}