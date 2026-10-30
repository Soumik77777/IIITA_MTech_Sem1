// Question 2: For a given binary tree, write a program to count the total number of nodes, internal nodes and external nodes.

#include <stdio.h>
#include <stdlib.h>

struct Node
{
    int data;
    struct Node *left;
    struct Node *right;
};

struct Node *createNode(int value)
{
    struct Node *newNode = (struct Node *)malloc(sizeof(struct Node));

    newNode->data = value;
    newNode->left = NULL;
    newNode->right = NULL;

    return newNode;
}

struct Node *createTree()
{
    int value;

    printf("Enter node value (-1 for no node): ");
    scanf("%d", &value);

    if (value == -1)
        return NULL;

    struct Node *root = createNode(value);

    printf("Left child of %d:\n", value);
    root->left = createTree();

    printf("Right child of %d:\n", value);
    root->right = createTree();

    return root;
}

int countNodes(struct Node *root)
{
    if (root == NULL)
        return 0;

    return 1 + countNodes(root->left) + countNodes(root->right);
}

int countInternal(struct Node *root)
{
    if (root == NULL)
        return 0;

    if (root->left == NULL && root->right == NULL)
        return 0;

    return 1 + countInternal(root->left) + countInternal(root->right);
}

int countExternal(struct Node *root)
{
    if (root == NULL)
        return 0;

    if (root->left == NULL && root->right == NULL)
        return 1;

    return countExternal(root->left) + countExternal(root->right);
}

void freeTree(struct Node *root)
{
    if (root == NULL)
        return;

    freeTree(root->left);
    freeTree(root->right);
    free(root);
}

int main()
{
    struct Node *root;

    printf("Create the binary tree:\n");
    root = createTree();

    printf("Total nodes: %d\n", countNodes(root));
    printf("Internal nodes: %d\n", countInternal(root));
    printf("External nodes: %d\n", countExternal(root));

    freeTree(root);

    return 0;
}