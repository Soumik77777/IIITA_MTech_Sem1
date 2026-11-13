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

int find_level(Node *root, int value, int level) {
    if (root == NULL) {
        return -1;
    }
    if (root->data == value) {
        return level;
    }
    if (value < root->data) {
        return find_level(root->left, value, level + 1);
    }
    return find_level(root->right, value, level + 1);
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
    int value;
    int level;

    for (size_t i = 0; i < count; i++) {
        root = insert(root, values[i]);
    }

    printf("Enter the element: ");
    if (scanf("%d", &value) != 1) {
        free_tree(root);
        return 0;
    }

    level = find_level(root, value, 0);
    if (level == -1) {
        printf("Element not found in the tree.\n");
    } else {
        printf("Level of %d is %d.\n", value, level);
    }

    free_tree(root);
    return 0;
}
