#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int vertices;
    int edges;
    int start;
    int **adj;
    int *visited;
    int *queue;
    int front = 0;
    int rear = 0;

    printf("Enter the number of vertices and edges: ");
    if (scanf("%d %d", &vertices, &edges) != 2 ||
        vertices <= 0 || edges < 0)
        return EXIT_FAILURE;

    adj = malloc((size_t)vertices * sizeof(*adj));
    visited = calloc((size_t)vertices, sizeof(*visited));
    queue = malloc((size_t)vertices * sizeof(*queue));

    if (adj == NULL || visited == NULL || queue == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        free(adj);
        free(visited);
        free(queue);
        return EXIT_FAILURE;
    }

    for (int i = 0; i < vertices; i++) {
        adj[i] = calloc((size_t)vertices, sizeof(*adj[i]));
        if (adj[i] == NULL) {
            fprintf(stderr, "Memory allocation failed\n");
            for (int j = 0; j < i; j++)
                free(adj[j]);
            free(adj);
            free(visited);
            free(queue);
            return EXIT_FAILURE;
        }
    }

    printf("Enter the edges (u v):\n");
    for (int i = 0; i < edges; i++) {
        int u;
        int v;
        if (scanf("%d %d", &u, &v) != 2 ||
            u < 0 || u >= vertices || v < 0 || v >= vertices) {
            fprintf(stderr, "Invalid edge\n");
            for (int j = 0; j < vertices; j++)
                free(adj[j]);
            free(adj);
            free(visited);
            free(queue);
            return EXIT_FAILURE;
        }
        adj[u][v] = 1;
        adj[v][u] = 1;
    }

    printf("Enter the starting vertex: ");
    if (scanf("%d", &start) != 1 || start < 0 || start >= vertices) {
        fprintf(stderr, "Invalid starting vertex\n");
        for (int i = 0; i < vertices; i++)
            free(adj[i]);
        free(adj);
        free(visited);
        free(queue);
        return EXIT_FAILURE;
    }

    visited[start] = 1;
    queue[rear++] = start;

    printf("BFS traversal: ");
    while (front < rear) {
        int current = queue[front++];
        printf("%d ", current);

        for (int i = 0; i < vertices; i++) {
            if (adj[current][i] && !visited[i]) {
                visited[i] = 1;
                queue[rear++] = i;
            }
        }
    }
    printf("\n");

    for (int i = 0; i < vertices; i++)
        free(adj[i]);
    free(adj);
    free(visited);
    free(queue);
    return 0;
}
