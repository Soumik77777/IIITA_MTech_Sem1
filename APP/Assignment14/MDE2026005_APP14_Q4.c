#include <stdio.h>
#include <stdlib.h>

typedef struct Node {
    int data;
    struct Node *left;
    struct Node *right;
} Node;

Node *create_node(int value) {
    Node *node = malloc(sizeof(*node));
    if (node == NULL) {
        fprintf(stderr, "Memory allocation failed.\n");
        exit(EXIT_FAILURE);
    }
    node->data = value;
    node->left = NULL;
    node->right = NULL;
    return node;
}

Node *insert(Node *root, int value) {
    if (root == NULL) {
        return create_node(value);
    }
    if (value < root->data) {
        root->left = insert(root->left, value);
    } else if (value > root->data) {
        root->right = insert(root->right, value);
    }
    return root;
}

int largest_element(Node *root) {
    while (root->right != NULL) {
        root = root->right;
    }
    return root->data;
}

void free_tree(Node *root) {
    if (root != NULL) {
        free_tree(root->left);
        free_tree(root->right);
        free(root);
    }
}

int main(void) {
    int values[] = {50, 10, 20, 30, 5, 90, 80, 100, 85};
    size_t count = sizeof(values) / sizeof(values[0]);
    Node *root = NULL;

    for (size_t i = 0; i < count; i++) {
        root = insert(root, values[i]);
    }

    if (root == NULL) {
        printf("Tree is empty.\n");
    } else {
        printf("Largest element in the BST is %d.\n", largest_element(root));
    }

    free_tree(root);
    return 0;
}
