#ifndef LINKED_LIST_H
#define LINKED_LIST_H

/* 双向链表 —— AI 对话历史存储
 *
 * 每个节点存储一条聊天消息（用户或 AI），支持：
 *   - 追加/插入/删除节点
 *   - 按 ID 查找
 *   - 全量导出为 JSON 数组
 *   - 从 JSON 数组批量导入
 */

typedef struct ChatNode {
    int id;                    /* 消息唯一 ID（自增） */
    char role[16];             /* "user" 或 "assistant" */
    char *content;             /* 消息正文（动态分配） */
    long long timestamp;       /* Unix 时间戳 */
    struct ChatNode *prev;
    struct ChatNode *next;
} ChatNode;

typedef struct {
    ChatNode *head;
    ChatNode *tail;
    int size;
    int next_id;
} ChatList;

/* 创建 / 销毁 */
ChatList* chat_list_create(void);
void chat_list_destroy(ChatList *list);

/* 追加消息到末尾，返回新节点 ID */
int  chat_list_append(ChatList *list, const char *role, const char *content, long long timestamp);

/* 插入消息到开头 */
int  chat_list_prepend(ChatList *list, const char *role, const char *content, long long timestamp);

/* 按 ID 删除节点，返回 1 成功 / 0 未找到 */
int  chat_list_delete_by_id(ChatList *list, int id);

/* 按 ID 查找节点（返回节点指针，勿 free） */
ChatNode* chat_list_find_by_id(ChatList *list, int id);

/* 导出为 JSON 数组字符串（调用者需 free） */
char* chat_list_to_json(const ChatList *list);

/* 从 JSON 数组批量导入（会先清空现有数据） */
int  chat_list_from_json(ChatList *list, const char *json);

/* 清空链表 */
void chat_list_clear(ChatList *list);

/* 返回节点数 */
int  chat_list_size(const ChatList *list);

/* ---------- 处理 main.c 路由的入口 ---------- */
/* 返回 JSON 结果字符串（调用者需 free），出错返回 NULL */
char* linked_list_handle(const char *action, const char *data_json);

#endif /* LINKED_LIST_H */
