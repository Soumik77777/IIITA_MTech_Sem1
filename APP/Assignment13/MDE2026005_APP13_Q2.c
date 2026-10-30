#include <stdio.h>
#include <stdlib.h>

typedef struct TreeNode {
    int value;
    char op;
    int is_operator;
    struct TreeNode *left;
    struct TreeNode *right;
} TreeNode;

static TreeNode *create_value_node(int value)
{
    TreeNode *node = malloc(sizeof(*node));
    if (node == NULL) {
        return NULL;
    }

    node->value = value;
    node->op = '\0';
    node->is_operator = 0;
    node->left = NULL;
    node->right = NULL;
    return node;
}

static TreeNode *create_operator_node(char op, TreeNode *left, TreeNode *right)
{
    TreeNode *node = malloc(sizeof(*node));
    if (node == NULL) {
        return NULL;
    }

    node->value = 0;
    node->op = op;
    node->is_operator = 1;
    node->left = left;
    node->right = right;
    return node;
}

/* Builds: 5 * (((3 * 4) + (6 / 2)) - (8 + 2)) */
static TreeNode *create_expression_tree(void)
{
    TreeNode *n5 = create_value_node(5);
    TreeNode *n3 = create_value_node(3);
    TreeNode *n4 = create_value_node(4);
    TreeNode *n6 = create_value_node(6);
    TreeNode *n2a = create_value_node(2);
    TreeNode *n8 = create_value_node(8);
    TreeNode *n2b = create_value_node(2);

    if (n5 == NULL || n3 == NULL || n4 == NULL || n6 == NULL ||
        n2a == NULL || n8 == NULL || n2b == NULL) {
        free(n5);
        free(n3);
        free(n4);
        free(n6);
        free(n2a);
        free(n8);
        free(n2b);
        return NULL;
    }

    TreeNode *multiply1 = create_operator_node('*', n3, n4);
    if (multiply1 == NULL) {
        free(n5); free(n3); free(n4); free(n6); free(n2a); free(n8); free(n2b);
        return NULL;
    }

    TreeNode *divide = create_operator_node('/', n6, n2a);
    if (divide == NULL) {
        free(n5); free(multiply1); free(n6); free(n2a); free(n8); free(n2b);
        return NULL;
    }

    TreeNode *add1 = create_operator_node('+', multiply1, divide);
    if (add1 == NULL) {
        free(n5); free(multiply1); free(divide); free(n8); free(n2b);
        return NULL;
    }

    TreeNode *add2 = create_operator_node('+', n8, n2b);
    if (add2 == NULL) {
        free(n5); free(add1); free(n8); free(n2b);
        return NULL;
    }

    TreeNode *subtract = create_operator_node('-', add1, add2);
    if (subtract == NULL) {
        free(n5); free(add1); free(add2);
        return NULL;
    }

    TreeNode *root = create_operator_node('*', n5, subtract);
    if (root == NULL) {
        free(n5);
        free(subtract);
        return NULL;
    }

    return root;
}

static void free_tree(TreeNode *root)
{
    if (root == NULL) {
        return;
    }

    free_tree(root->left);
    free_tree(root->right);
    free(root);
}

static void preorder(const TreeNode *root)
{
    if (root == NULL) {
        return;
    }

    if (root->is_operator) {
        printf("%c ", root->op);
    } else {
        printf("%d ", root->value);
    }
    preorder(root->left);
    preorder(root->right);
}

static void inorder(const TreeNode *root)
{
    if (root == NULL) {
        return;
    }

    inorder(root->left);
    if (root->is_operator) {
        printf("%c ", root->op);
    } else {
        printf("%d ", root->value);
    }
    inorder(root->right);
}

static void postorder(const TreeNode *root)
{
    if (root == NULL) {
        return;
    }

    postorder(root->left);
    postorder(root->right);
    if (root->is_operator) {
        printf("%c ", root->op);
    } else {
        printf("%d ", root->value);
    }
}

int main(void)
{
    TreeNode *root = create_expression_tree();
    if (root == NULL) {
        fprintf(stderr, "Error: unable to create the expression tree.\n");
        return EXIT_FAILURE;
    }

    printf("Preorder:  ");
    preorder(root);
    printf("\n");

    printf("Inorder:   ");
    inorder(root);
    printf("\n");

    printf("Postorder: ");
    postorder(root);
    printf("\n");

    free_tree(root);
    return EXIT_SUCCESS;
}
