/*
 * queue.h — 队列数据结构（用于 AI 请求排队管理）
 *
 * 功能：
 *   - 基于链表实现的 FIFO 队列
 *   - 支持 JSON 文件持久化（跨 subprocess 调用保持状态）
 *   - 提供入队、出队、查看队首、大小、判空、清空等操作
 *
 * 在 CampusAI 项目中的作用：
 *   当多个用户同时请求 AI 分析时，请求先入队，
 *   然后按 FIFO 顺序逐一处理，避免 API 并发调用超限。
 *
 * 编译：见 Makefile
 * 用法：./campus_lib queue < queue_data.json
 */

#ifndef QUEUE_H
#define QUEUE_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ============================================================
 * 队列节点
 * ============================================================ */
typedef struct QNode {
    char *data;            /* JSON 字符串数据（堆分配） */
    struct QNode *next;    /* 指向下一个节点 */
} QNode;

/* ============================================================
 * 队列结构
 * ============================================================ */
typedef struct {
    QNode *front;          /* 队首（出队端） */
    QNode *rear;           /* 队尾（入队端） */
    int size;              /* 当前元素个数 */
} Queue;

/* ============================================================
 * 队列操作
 * ============================================================ */

/** 创建空队列，返回堆上的 Queue 指针 */
Queue* queue_create(void);

/** 销毁队列，释放所有节点和数据内存 */
void queue_destroy(Queue *q);

/**
 * 入队：将 data 的副本加入队尾。
 * 返回 0 成功，-1 失败（内存不足）。
 */
int queue_enqueue(Queue *q, const char *data);

/**
 * 出队：移除并返回队首的数据指针。
 * 调用者负责 free() 返回的字符串。
 * 队列为空时返回 NULL。
 */
char* queue_dequeue(Queue *q);

/**
 * 查看队首：返回队首数据的指针（只读副本）。
 * 调用者负责 free() 返回的字符串。
 * 队列为空时返回 NULL。
 */
char* queue_peek(const Queue *q);

/** 队列是否为空：空返回 1，非空返回 0 */
int queue_is_empty(const Queue *q);

/** 返回队列当前元素个数 */
int queue_size(const Queue *q);

/** 清空队列：移除所有元素并释放内存 */
void queue_clear(Queue *q);

/* ============================================================
 * 持久化（JSON 文件读写）
 * ============================================================ */

/**
 * 将队列序列化为 JSON 数组字符串。
 * 格式：["item1_json", "item2_json", ...]
 * 调用者负责 free() 返回值。
 */
char* queue_to_json(const Queue *q);

/**
 * 从 JSON 数组字符串恢复队列。
 * 会先清空 q，然后逐项入队。
 * 返回 0 成功，-1 格式错误。
 */
int queue_from_json(Queue *q, const char *json_str);

#endif /* QUEUE_H */
