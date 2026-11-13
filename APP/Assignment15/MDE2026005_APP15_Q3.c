#include <stdio.h>
#include <stdlib.h>

typedef struct Node {
    int data;
    int height;
    struct Node *left;
    struct Node *right;
} Node;

int height(Node *root) {
    return root ? root->height : 0;
}

int max(int a, int b) {
    return a > b ? a : b;
}

int balance(Node *root) {
    return root ? height(root->left) - height(root->right) : 0;
}

Node *createNode(int data) {
    Node *node = malloc(sizeof(Node));
    node->data = data;
    node->height = 1;
    node->left = NULL;
    node->right = NULL;
    return node;
}

Node *rightRotate(Node *y) {
    Node *x = y->left;
    Node *t = x->right;

    x->right = y;
    y->left = t;

    y->height = 1 + max(height(y->left), height(y->right));
    x->height = 1 + max(height(x->left), height(x->right));

    return x;
}

Node *leftRotate(Node *x) {
    Node *y = x->right;
    Node *t = y->left;

    y->left = x;
    x->right = t;

    x->height = 1 + max(height(x->left), height(x->right));
    y->height = 1 + max(height(y->left), height(y->right));

    return y;
}

Node *rebalance(Node *root) {
    if (!root)
        return root;

    root->height = 1 + max(height(root->left), height(root->right));

    int bf = balance(root);

    if (bf > 1 && balance(root->left) >= 0)
        return rightRotate(root);

    if (bf > 1 && balance(root->left) < 0) {
        root->left = leftRotate(root->left);
        return rightRotate(root);
    }

    if (bf < -1 && balance(root->right) <= 0)
        return leftRotate(root);

    if (bf < -1 && balance(root->right) > 0) {
        root->right = rightRotate(root->right);
        return leftRotate(root);
    }

    return root;
}

Node *insert(Node *root, int data) {
    if (!root)
        return createNode(data);

    if (data < root->data)
        root->left = insert(root->left, data);
    else if (data > root->data)
        root->right = insert(root->right, data);
    else
        return root;

    return rebalance(root);
}

Node *minValueNode(Node *root) {
    Node *current = root;

    while (current->left)
        current = current->left;

    return current;
}

Node *deleteNode(Node *root, int data) {
    if (!root)
        return NULL;

    if (data < root->data) {
        root->left = deleteNode(root->left, data);
    }
    else if (data > root->data) {
        root->right = deleteNode(root->right, data);
    }
    else {
        if (!root->left || !root->right) {
            Node *temp = root->left ? root->left : root->right;
            free(root);
            return temp;
        }

        Node *temp = minValueNode(root->right);
        root->data = temp->data;
        root->right = deleteNode(root->right, temp->data);
    }

    return rebalance(root);
}

void inorder(Node *root) {
    if (!root)
        return;

    inorder(root->left);
    printf("%d ", root->data);
    inorder(root->right);
}

void freeTree(Node *root) {
    if (!root)
        return;

    freeTree(root->left);
    freeTree(root->right);
    free(root);
}

int main() {
    int values[] = {50, 10, 20, 30, 5, 90, 80, 100, 85};
    int n = sizeof(values) / sizeof(values[0]);

    Node *root = NULL;

    for (int i = 0; i < n; i++)
        root = insert(root, values[i]);

    printf("Initial tree: ");
    inorder(root);
    printf("\n");

    root = deleteNode(root, 20);
    printf("After deleting 20: ");
    inorder(root);
    printf("\n");

    root = deleteNode(root, 90);
    printf("After deleting 90: ");
    inorder(root);
    printf("\n");

    root = insert(root, 75);
    printf("After inserting 75: ");
    inorder(root);
    printf("\n");

    root = deleteNode(root, 30);
    printf("After deleting 30: ");
    inorder(root);
    printf("\n");

    freeTree(root);
    return 0;
}