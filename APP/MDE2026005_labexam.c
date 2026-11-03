#include <stdio.h>
#include <stdlib.h>

struct Node {
    int data;
    struct Node *leftChild;
    struct Node *rightChild;
};


struct Node* mirror (struct Node *root) {
    if (root == NULL) {
        return NULL;
    }

    struct Node *temp = root->leftChild;
    root->leftChild = root->rightChild;
    root->rightChild = temp;

    mirror(root->leftChild);
    mirror(root->rightChild);

    return root;
}


struct Node* createNode (int value) {
    struct Node *newNode = malloc(sizeof(struct Node));

    if (newNode == NULL) {
        printf("Memory allocation failed");
        exit(1);
    }

    newNode->data = value;
    newNode->leftChild = NULL;
    newNode->rightChild = NULL;

    return newNode;
}


struct Node * createTree() {
    int value;
    printf("Enter value (-1 for NULL): ");
    scanf("%d", &value);

    if (value == -1) {
        return NULL;
    }

    struct Node *root;

    root = createNode(value);

    printf("Enter left child of %d: \n", root->data);
    root->leftChild = createTree();

    printf("Enter right child of %d: \n", root->data);
    root->rightChild = createTree();

    return root;
}


void dfs_traversal_inorder (struct Node *root) {
    if (root == NULL) {
        return;
    }

    dfs_traversal_inorder(root->leftChild);
    printf("%d", root->data);
    dfs_traversal_inorder(root->rightChild);
}


void main () {
    struct Node *root = createTree();

    printf("Given Binary Tree Inorder Traversal:\n");
    dfs_traversal_inorder(root);
    printf("\n");

    // MIRROR
    struct Node *mirror_root = mirror(root);

    printf("Mirror Image of Given Binary Tree, Inorder Traversal:\n");
    dfs_traversal_inorder(root);
    printf("\n");

}