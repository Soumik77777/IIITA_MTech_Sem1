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

Node *readTree(void) {
    int value;
    if (scanf("%d", &value) != 1)
        exit(EXIT_FAILURE);
    if (value == -1)
        return NULL;

    Node *root = createNode(value);
    root->left = readTree();
    root->right = readTree();
    return root;
}

int identical(Node *a, Node *b) {
    if (a == NULL && b == NULL)
        return 1;
    if (a == NULL || b == NULL)
        return 0;
    return a->data == b->data &&
           identical(a->left, b->left) &&
           identical(a->right, b->right);
}

int isSubtree(Node *tree, Node *subtree) {
    if (subtree == NULL)
        return 1;
    if (tree == NULL)
        return 0;
    if (identical(tree, subtree))
        return 1;
    return isSubtree(tree->left, subtree) ||
           isSubtree(tree->right, subtree);
}

void freeTree(Node *root) {
    if (root == NULL)
        return;
    freeTree(root->left);
    freeTree(root->right);
    free(root);
}

int main(void) {
    Node *tree;
    Node *subtree;

    printf("Enter the first tree in preorder (-1 for NULL):\n");
    tree = readTree();

    printf("Enter the second tree in preorder (-1 for NULL):\n");
    subtree = readTree();

    if (isSubtree(tree, subtree))
        printf("The second tree is a subtree of the first tree.\n");
    else
        printf("The second tree is not a subtree of the first tree.\n");

    freeTree(tree);
    freeTree(subtree);
    return 0;
}
