#include <stdio.h>
#include <stdlib.h>

typedef struct Node {
    int data;
    struct Node *left;
    struct Node *right;
} Node;

Node *createNode(int data) {
    Node *node = malloc(sizeof(Node));
    if (node == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        exit(EXIT_FAILURE);
    }
    node->data = data;
    node->left = NULL;
    node->right = NULL;
    return node;
}

Node *insert(Node *root, int data) {
    if (root == NULL)
        return createNode(data);

    if (data < root->data)
        root->left = insert(root->left, data);
    else if (data > root->data)
        root->right = insert(root->right, data);

    return root;
}

int search(Node *root, int data) {
    while (root != NULL) {
        if (data == root->data)
            return 1;
        if (data < root->data)
            root = root->left;
        else
            root = root->right;
    }
    return 0;
}

Node *lowestCommonAncestor(Node *root, int n1, int n2) {
    while (root != NULL) {
        if (n1 < root->data && n2 < root->data)
            root = root->left;
        else if (n1 > root->data && n2 > root->data)
            root = root->right;
        else
            return root;
    }
    return NULL;
}

void freeTree(Node *root) {
    if (root == NULL)
        return;
    freeTree(root->left);
    freeTree(root->right);
    free(root);
}

int main(void) {
    Node *root = NULL;
    int n;
    int value;
    int n1;
    int n2;

    printf("Enter the number of nodes: ");
    if (scanf("%d", &n) != 1 || n < 0)
        return EXIT_FAILURE;

    printf("Enter the node values: ");
    for (int i = 0; i < n; i++) {
        if (scanf("%d", &value) != 1) {
            freeTree(root);
            return EXIT_FAILURE;
        }
        root = insert(root, value);
    }

    printf("Enter the two nodes: ");
    if (scanf("%d %d", &n1, &n2) != 2) {
        freeTree(root);
        return EXIT_FAILURE;
    }

    if (!search(root, n1) || !search(root, n2)) {
        printf("One or both nodes are not present in the BST.\n");
    } else {
        Node *lca = lowestCommonAncestor(root, n1, n2);
        if (lca != NULL)
            printf("Lowest common ancestor: %d\n", lca->data);
    }

    freeTree(root);
    return 0;
}
