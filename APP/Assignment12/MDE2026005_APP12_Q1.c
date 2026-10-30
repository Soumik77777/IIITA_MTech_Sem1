// Question 1: Write a C program to represent a general tree and perform the following operations:
// a. Find the parent of a given node.
// b. Display all children of a given node.
// c. Count the total number of leaf nodes in the tree.

#include <stdio.h>
#include <stdlib.h>

struct Node
{
    int data;
    struct Node *firstChild;
    struct Node *nextSibling;
};

struct Node *createNode(int value)
{
    struct Node *newNode = (struct Node *)malloc(sizeof(struct Node));

    if (newNode == NULL)
    {
        printf("Memory allocation failed!\n");
        exit(1);
    }

    newNode->data = value;
    newNode->firstChild = NULL;
    newNode->nextSibling = NULL;

    return newNode;
}

struct Node *findNode(struct Node *root, int value)
{
    if (root == NULL)
        return NULL;

    if (root->data == value)
        return root;

    struct Node *temp = findNode(root->firstChild, value);

    if (temp != NULL)
        return temp;

    return findNode(root->nextSibling, value);
}

void addChild(struct Node *root, int parent, int value)
{
    struct Node *parentNode = findNode(root, parent);

    if (parentNode == NULL)
    {
        printf("Parent not found!\n");
        return;
    }

    if (findNode(root, value) != NULL)
    {
        printf("Node already exists!\n");
        return;
    }

    struct Node *newNode = createNode(value);

    if (parentNode->firstChild == NULL)
        parentNode->firstChild = newNode;
    else
    {
        struct Node *temp = parentNode->firstChild;

        while (temp->nextSibling != NULL)
            temp = temp->nextSibling;

        temp->nextSibling = newNode;
    }
}

int findParent(struct Node *root, int value)
{
    if (root == NULL)
        return 0;

    struct Node *temp = root->firstChild;

    while (temp != NULL)
    {
        if (temp->data == value)
        {
            printf("Parent: %d\n", root->data);
            return 1;
        }

        if (findParent(temp, value))
            return 1;

        temp = temp->nextSibling;
    }

    return 0;
}

void displayChildren(struct Node *root, int value)
{
    struct Node *node = findNode(root, value);

    if (node == NULL)
    {
        printf("Node not found!\n");
        return;
    }

    struct Node *temp = node->firstChild;

    if (temp == NULL)
    {
        printf("No children.\n");
        return;
    }

    printf("Children: ");

    while (temp != NULL)
    {
        printf("%d ", temp->data);
        temp = temp->nextSibling;
    }

    printf("\n");
}

int countLeaves(struct Node *root)
{
    if (root == NULL)
        return 0;

    if (root->firstChild == NULL)
        return 1;

    int count = 0;
    struct Node *temp = root->firstChild;

    while (temp != NULL)
    {
        count += countLeaves(temp);
        temp = temp->nextSibling;
    }

    return count;
}

void freeTree(struct Node *root)
{
    if (root == NULL)
        return;

    freeTree(root->firstChild);
    freeTree(root->nextSibling);
    free(root);
}

int main()
{
    struct Node *root;
    int n, i, parent, value, choice;

    printf("Enter root value: ");
    scanf("%d", &value);
    root = createNode(value);

    printf("Enter number of edges: ");
    scanf("%d", &n);

    if (n < 0)
    {
        printf("Invalid number of edges!\n");
        freeTree(root);
        return 1;
    }

    for (i = 0; i < n; i++)
    {
        printf("Enter parent and child: ");
        scanf("%d %d", &parent, &value);

        addChild(root, parent, value);
    }

    while (1)
    {
        printf("\n1. FIND PARENT\n2. DISPLAY CHILDREN\n3. COUNT LEAF NODES\n4. EXIT\n");
        printf("Enter your choice: ");
        scanf("%d", &choice);

        switch (choice)
        {
            case 1:
                printf("Enter node: ");
                scanf("%d", &value);

                if (root->data == value)
                    printf("Root has no parent.\n");
                else if (!findParent(root, value))
                    printf("Node not found!\n");

                break;

            case 2:
                printf("Enter node: ");
                scanf("%d", &value);
                displayChildren(root, value);
                break;

            case 3:
                printf("Total leaf nodes: %d\n", countLeaves(root));
                break;

            case 4:
                freeTree(root);
                return 0;

            default:
                printf("Invalid choice!\n");
        }
    }
}