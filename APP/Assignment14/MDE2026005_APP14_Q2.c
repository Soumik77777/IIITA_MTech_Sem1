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

Node *search(Node *root, int value) {
    if (root == NULL || root->data == value) {
        return root;
    }
    if (value < root->data) {
        return search(root->left, value);
    }
    return search(root->right, value);
}

Node *minimum_node(Node *root) {
    while (root != NULL && root->left != NULL) {
        root = root->left;
    }
    return root;
}

Node *delete_node(Node *root, int value) {
    if (root == NULL) {
        return NULL;
    }
    if (value < root->data) {
        root->left = delete_node(root->left, value);
    } else if (value > root->data) {
        root->right = delete_node(root->right, value);
    } else {
        if (root->left == NULL) {
            Node *right = root->right;
            free(root);
            return right;
        }
        if (root->right == NULL) {
            Node *left = root->left;
            free(root);
            return left;
        }
        Node *successor = minimum_node(root->right);
        root->data = successor->data;
        root->right = delete_node(root->right, successor->data);
    }
    return root;
}

void preorder(Node *root) {
    if (root != NULL) {
        printf("%d ", root->data);
        preorder(root->left);
        preorder(root->right);
    }
}

void inorder(Node *root) {
    if (root != NULL) {
        inorder(root->left);
        printf("%d ", root->data);
        inorder(root->right);
    }
}

void postorder(Node *root) {
    if (root != NULL) {
        postorder(root->left);
        postorder(root->right);
        printf("%d ", root->data);
    }
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
    int choice;
    int value;

    for (size_t i = 0; i < count; i++) {
        root = insert(root, values[i]);
    }

    do {
        printf("\n1. Preorder\n2. Inorder\n3. Postorder\n4. Search\n5. Insert\n6. Delete\n0. Exit\nEnter choice: ");
        if (scanf("%d", &choice) != 1) {
            free_tree(root);
            return 0;
        }

        switch (choice) {
            case 1:
                preorder(root);
                printf("\n");
                break;
            case 2:
                inorder(root);
                printf("\n");
                break;
            case 3:
                postorder(root);
                printf("\n");
                break;
            case 4:
                printf("Enter value to search: ");
                if (scanf("%d", &value) != 1) {
                    free_tree(root);
                    return 0;
                }
                printf(search(root, value) != NULL ? "Element found.\n" : "Element not found.\n");
                break;
            case 5:
                printf("Enter value to insert: ");
                if (scanf("%d", &value) != 1) {
                    free_tree(root);
                    return 0;
                }
                if (search(root, value) != NULL) {
                    printf("Duplicate values are not inserted.\n");
                } else {
                    root = insert(root, value);
                    printf("Element inserted.\n");
                }
                break;
            case 6:
                printf("Enter value to delete: ");
                if (scanf("%d", &value) != 1) {
                    free_tree(root);
                    return 0;
                }
                if (search(root, value) == NULL) {
                    printf("Element not found.\n");
                } else {
                    root = delete_node(root, value);
                    printf("Element deleted.\n");
                }
                break;
            case 0:
                break;
            default:
                printf("Invalid choice.\n");
        }
    } while (choice != 0);

    free_tree(root);
    return 0;
}
