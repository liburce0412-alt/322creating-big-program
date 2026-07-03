#ifndef QUEUE_H
#define QUEUE_H

/* 队列 —— AI 请求排队管理
 *
 * 先进先出（FIFO），用于管理对 DeepSeek / Gemini 的并发请求。
 * 底层使用链表实现，支持：
 *   - 入队 / 出队
 *   - 查看队首（不删除）
 *   - 查看队列大小 / 是否为空
 *   - 清空队列
 */

typedef struct QueueNode {
    char   request_id[64];     /* 请求唯一 ID */
    char   model[32];          /* 模型名称 "deepseek" / "gemini" */
    char   prompt_hash[64];    /* 请求 prompt 的哈希（用于去重） */
    int    priority;           /* 优先级（越小越优先，0 最高） */
    long long enqueued_at;     /* 入队时间戳 */
    struct QueueNode *next;
} QueueNode;

typedef struct {
    QueueNode *front;
    QueueNode *rear;
    int size;
} AIQueue;

/* 创建 / 销毁 */
AIQueue* queue_create(void);
void queue_destroy(AIQueue *q);

/* 入队，返回新队列大小 */
int  queue_enqueue(AIQueue *q, const char *request_id, const char *model,
                   const char *prompt_hash, int priority, long long timestamp);

/* 出队，返回出队节点的 JSON 字符串（调用者需 free），队空返回 NULL */
char* queue_dequeue(AIQueue *q);

/* 查看队首（JSON 字符串），不删除，队空返回 NULL */
char* queue_peek(const AIQueue *q);

/* 是否为空 */
int  queue_is_empty(const AIQueue *q);

/* 队列大小 */
int  queue_size(const AIQueue *q);

/* 清空 */
void queue_clear(AIQueue *q);

/* ---------- 处理 main.c 路由的入口 ---------- */
char* queue_handle(const char *action, const char *data_json);

#endif /* QUEUE_H */
