#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "queue.h"

/* ========== 内部 JSON 辅助函数 ========== */

static char* json_extract_string(const char *json, const char *key) {
    if (!json || !key) return NULL;
    char search[128];
    snprintf(search, sizeof(search), "\"%s\"", key);
    const char *pos = strstr(json, search);
    if (!pos) return NULL;
    pos += strlen(search);
    while (*pos && (*pos == ':' || *pos == ' ' || *pos == '\t')) pos++;
    if (*pos != '"') return NULL;
    pos++;
    const char *end = pos;
    while (*end && *end != '"') {
        if (*end == '\\' && *(end + 1)) end++;
        end++;
    }
    if (*end != '"') return NULL;
    size_t len = end - pos;
    char *result = (char*) malloc(len + 1);
    if (!result) return NULL;
    size_t j = 0;
    for (size_t i = 0; i < len; i++) {
        if (pos[i] == '\\' && i + 1 < len) {
            i++;
            switch (pos[i]) {
                case 'n':  result[j++] = '\n'; break;
                case 't':  result[j++] = '\t'; break;
                case '"':  result[j++] = '"';  break;
                case '\\': result[j++] = '\\'; break;
                default:   result[j++] = pos[i]; break;
            }
        } else {
            result[j++] = pos[i];
        }
    }
    result[j] = '\0';
    return result;
}

static int json_extract_int(const char *json, const char *key, int default_val) {
    if (!json || !key) return default_val;
    char search[128];
    snprintf(search, sizeof(search), "\"%s\"", key);
    const char *pos = strstr(json, search);
    if (!pos) return default_val;
    pos += strlen(search);
    while (*pos && (*pos == ':' || *pos == ' ' || *pos == '\t')) pos++;
    return atoi(pos);
}

static long long json_extract_long(const char *json, const char *key, long long default_val) {
    if (!json || !key) return default_val;
    char search[128];
    snprintf(search, sizeof(search), "\"%s\"", key);
    const char *pos = strstr(json, search);
    if (!pos) return default_val;
    pos += strlen(search);
    while (*pos && (*pos == ':' || *pos == ' ' || *pos == '\t')) pos++;
    return atoll(pos);
}

/* ========== 队列实现 ========== */

AIQueue* queue_create(void) {
    AIQueue *q = (AIQueue*) malloc(sizeof(AIQueue));
    if (!q) return NULL;
    q->front = NULL;
    q->rear = NULL;
    q->size = 0;
    return q;
}

void queue_destroy(AIQueue *q) {
    if (!q) return;
    queue_clear(q);
    free(q);
}

void queue_clear(AIQueue *q) {
    if (!q) return;
    QueueNode *cur = q->front;
    while (cur) {
        QueueNode *next = cur->next;
        free(cur);
        cur = next;
    }
    q->front = NULL;
    q->rear = NULL;
    q->size = 0;
}

int queue_enqueue(AIQueue *q, const char *request_id, const char *model,
                  const char *prompt_hash, int priority, long long timestamp) {
    if (!q) return -1;
    QueueNode *node = (QueueNode*) malloc(sizeof(QueueNode));
    if (!node) return -1;
    strncpy(node->request_id, request_id, sizeof(node->request_id) - 1);
    node->request_id[sizeof(node->request_id) - 1] = '\0';
    strncpy(node->model, model, sizeof(node->model) - 1);
    node->model[sizeof(node->model) - 1] = '\0';
    strncpy(node->prompt_hash, prompt_hash, sizeof(node->prompt_hash) - 1);
    node->prompt_hash[sizeof(node->prompt_hash) - 1] = '\0';
    node->priority = priority;
    node->enqueued_at = timestamp;
    node->next = NULL;

    if (q->rear) {
        q->rear->next = node;
    } else {
        q->front = node;
    }
    q->rear = node;
    q->size++;
    return q->size;
}

char* queue_dequeue(AIQueue *q) {
    if (!q || !q->front) return NULL;
    QueueNode *node = q->front;
    q->front = node->next;
    if (!q->front) q->rear = NULL;
    q->size--;

    char buf[512];
    snprintf(buf, sizeof(buf),
        "{\"request_id\":\"%s\",\"model\":\"%s\",\"prompt_hash\":\"%s\","
        "\"priority\":%d,\"enqueued_at\":%lld}",
        node->request_id, node->model, node->prompt_hash,
        node->priority, node->enqueued_at);
    free(node);
    return strdup(buf);
}

char* queue_peek(const AIQueue *q) {
    if (!q || !q->front) return NULL;
    QueueNode *node = q->front;
    char buf[512];
    snprintf(buf, sizeof(buf),
        "{\"request_id\":\"%s\",\"model\":\"%s\",\"prompt_hash\":\"%s\","
        "\"priority\":%d,\"enqueued_at\":%lld}",
        node->request_id, node->model, node->prompt_hash,
        node->priority, node->enqueued_at);
    return strdup(buf);
}

int queue_is_empty(const AIQueue *q) {
    return (q && q->size > 0) ? 0 : 1;
}

int queue_size(const AIQueue *q) {
    return q ? q->size : 0;
}

/* ========== main.c 路由入口 ========== */

char* queue_handle(const char *action, const char *data_json) {
    static AIQueue *q = NULL;
    if (!q) q = queue_create();

    if (!action) {
        return strdup("{\"error\":\"missing action\"}");
    }

    if (strcmp(action, "enqueue") == 0) {
        char *req_id   = json_extract_string(data_json, "request_id");
        char *model    = json_extract_string(data_json, "model");
        char *hash     = json_extract_string(data_json, "prompt_hash");
        int  priority  = json_extract_int(data_json, "priority", 0);
        long long ts   = json_extract_long(data_json, "timestamp", (long long) time(NULL));

        if (!req_id) {
            free(req_id); free(model); free(hash);
            return strdup("{\"error\":\"request_id required\"}");
        }
        int size = queue_enqueue(q, req_id ? req_id : "unknown",
                                    model ? model : "deepseek",
                                    hash ? hash : "",
                                    priority, ts);
        free(req_id); free(model); free(hash);
        char buf[128];
        snprintf(buf, sizeof(buf),
            "{\"enqueued\":true,\"size\":%d}", size);
        return strdup(buf);
    }

    if (strcmp(action, "dequeue") == 0) {
        char *result = queue_dequeue(q);
        if (!result) return strdup("{\"dequeued\":false,\"error\":\"queue is empty\"}");
        /* 包装一下 */
        size_t len = strlen(result) + 64;
        char *wrapped = (char*) malloc(len);
        snprintf(wrapped, len, "{\"dequeued\":true,\"item\":%s}", result);
        free(result);
        return wrapped;
    }

    if (strcmp(action, "peek") == 0) {
        char *result = queue_peek(q);
        if (!result) return strdup("{\"found\":false,\"error\":\"queue is empty\"}");
        size_t len = strlen(result) + 64;
        char *wrapped = (char*) malloc(len);
        snprintf(wrapped, len, "{\"found\":true,\"item\":%s}", result);
        free(result);
        return wrapped;
    }

    if (strcmp(action, "size") == 0) {
        char buf[64];
        snprintf(buf, sizeof(buf), "{\"size\":%d}", q->size);
        return strdup(buf);
    }

    if (strcmp(action, "is_empty") == 0) {
        char buf[64];
        snprintf(buf, sizeof(buf), "{\"is_empty\":%s}", q->size == 0 ? "true" : "false");
        return strdup(buf);
    }

    if (strcmp(action, "clear") == 0) {
        int old_size = q->size;
        queue_clear(q);
        char buf[128];
        snprintf(buf, sizeof(buf),
            "{\"cleared\":true,\"removed\":%d,\"size\":0}", old_size);
        return strdup(buf);
    }

    /* 批量导入（用于从数据库恢复队列） */
    if (strcmp(action, "from_array") == 0) {
        if (!data_json) return strdup("{\"error\":\"data required\"}");
        const char *arr = strchr(data_json, '[');
        if (!arr) return strdup("{\"imported\":0}");
        arr++;
        int count = 0;
        const char *p = arr;
        while (*p) {
            while (*p && *p != '{' && *p != ']') p++;
            if (*p == ']' || *p == '\0') break;
            const char *obj = p;
            int depth = 0;
            while (*p) {
                if (*p == '{') depth++;
                else if (*p == '}') { depth--; if (depth == 0) { p++; break; } }
                else if (*p == '"') { p++; while (*p && *p != '"') { if (*p == '\\') p++; if (*p) p++; } }
                p++;
            }
            char *rid = json_extract_string(obj, "request_id");
            char *mod = json_extract_string(obj, "model");
            char *ph  = json_extract_string(obj, "prompt_hash");
            int pri   = json_extract_int(obj, "priority", 0);
            long long ts = json_extract_long(obj, "enqueued_at", (long long) time(NULL));
            if (rid) {
                queue_enqueue(q, rid, mod ? mod : "deepseek", ph ? ph : "", pri, ts);
                count++;
            }
            free(rid); free(mod); free(ph);
        }
        char buf[128];
        snprintf(buf, sizeof(buf), "{\"imported\":%d,\"size\":%d}", count, q->size);
        return strdup(buf);
    }

    char buf[256];
    snprintf(buf, sizeof(buf), "{\"error\":\"unknown action: %s\"}", action);
    return strdup(buf);
}
