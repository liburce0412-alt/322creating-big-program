/*
 * queue.c — 队列数据结构实现（AI 请求排队管理）
 *
 * 编译：gcc -Wall -O2 -o campus_lib queue.c main.c
 *       或通过 Makefile: make
 *
 * 作为独立模块使用：
 *   echo '{"command":"enqueue","data":"{\"user_id\":1}"}' | ./campus_lib queue
 *
 * 协议（stdin/stdout JSON）：
 *   输入：{"command": "enqueue", "data": "<json_string>"}
 *         {"command": "dequeue"}
 *         {"command": "peek"}
 *         {"command": "size"}
 *         {"command": "is_empty"}
 *         {"command": "clear"}
 *
 *   输出：{"status": "ok", "result": ...}
 *         {"status": "error", "message": "..."}
 *
 * 持久化：队列数据保存在 queue_data.json 文件中
 *         每次操作前读取，操作后写回
 */

#include "queue.h"
#include <ctype.h>

/* ============================================================
 * 持久化文件路径
 * ============================================================ */
#define QUEUE_DATA_FILE "queue_data.json"


/* ============================================================
 * 辅助函数：安全字符串复制
 * ============================================================ */
static char* safe_strdup(const char *src) {
    if (!src) return NULL;
    size_t len = strlen(src);
    char *dst = (char*)malloc(len + 1);
    if (dst) {
        memcpy(dst, src, len + 1);
    }
    return dst;
}


/* ============================================================
 * 队列操作实现
 * ============================================================ */

Queue* queue_create(void) {
    Queue *q = (Queue*)malloc(sizeof(Queue));
    if (!q) return NULL;
    q->front = NULL;
    q->rear = NULL;
    q->size = 0;
    return q;
}


void queue_destroy(Queue *q) {
    if (!q) return;
    queue_clear(q);
    free(q);
}


int queue_enqueue(Queue *q, const char *data) {
    if (!q || !data) return -1;

    QNode *node = (QNode*)malloc(sizeof(QNode));
    if (!node) return -1;

    node->data = safe_strdup(data);
    if (!node->data) {
        free(node);
        return -1;
    }
    node->next = NULL;

    if (q->rear) {
        q->rear->next = node;
    } else {
        q->front = node;
    }
    q->rear = node;
    q->size++;

    return 0;
}


char* queue_dequeue(Queue *q) {
    if (!q || !q->front) return NULL;

    QNode *node = q->front;
    char *data = node->data;  /* 转移所有权给调用者 */

    q->front = node->next;
    if (!q->front) {
        q->rear = NULL;
    }
    q->size--;

    free(node);
    return data;
}


char* queue_peek(const Queue *q) {
    if (!q || !q->front) return NULL;
    return safe_strdup(q->front->data);
}


int queue_is_empty(const Queue *q) {
    return (!q || q->size == 0) ? 1 : 0;
}


int queue_size(const Queue *q) {
    return q ? q->size : 0;
}


void queue_clear(Queue *q) {
    if (!q) return;
    while (q->front) {
        char *data = queue_dequeue(q);
        free(data);
    }
}


/* ============================================================
 * JSON 序列化 / 反序列化
 *
 * 为保持项目零外部依赖的原则，这里实现一个最小化的 JSON
 * 字符串数组解析器。仅支持如下格式：
 *
 *   ["str1", "str2", "str3"]
 *
 * 其中每个字符串支持 \", \\, \n, \t 转义。
 * 这不是通用 JSON 解析器，只满足本项目的队列持久化需求。
 * ============================================================ */

/**
 * 将字符串中的特殊字符进行 JSON 转义，返回新分配的字符串。
 */
static char* json_escape(const char *src) {
    if (!src) return NULL;

    /* 先计算转义后需要的大小 */
    size_t len = 0;
    for (const char *p = src; *p; p++) {
        switch (*p) {
            case '"':  case '\\': len += 2; break;
            case '\n':              len += 2; break;
            case '\t':              len += 2; break;
            case '\r':              len += 2; break;
            default:                len += 1; break;
        }
    }

    char *dst = (char*)malloc(len + 1);
    if (!dst) return NULL;

    char *w = dst;
    for (const char *p = src; *p; p++) {
        switch (*p) {
            case '"':  *w++ = '\\'; *w++ = '"';  break;
            case '\\': *w++ = '\\'; *w++ = '\\'; break;
            case '\n': *w++ = '\\'; *w++ = 'n';  break;
            case '\t': *w++ = '\\'; *w++ = 't';  break;
            case '\r': *w++ = '\\'; *w++ = 'r';  break;
            default:   *w++ = *p;                 break;
        }
    }
    *w = '\0';
    return dst;
}


/**
 * 解析 JSON 转义字符，原地修改（结果不长于输入）。
 */
static void json_unescape_inplace(char *str) {
    if (!str) return;
    char *r = str;
    char *w = str;
    while (*r) {
        if (*r == '\\' && *(r + 1)) {
            r++;
            switch (*r) {
                case '"':  *w++ = '"';  break;
                case '\\': *w++ = '\\'; break;
                case 'n':  *w++ = '\n'; break;
                case 't':  *w++ = '\t'; break;
                case 'r':  *w++ = '\r'; break;
                default:   *w++ = '\\'; *w++ = *r; break;
            }
            r++;
        } else {
            *w++ = *r++;
        }
    }
    *w = '\0';
}


char* queue_to_json(const Queue *q) {
    if (!q) return safe_strdup("[]");

    /* 预估大小：每个元素加引号和逗号，外加 [] */
    size_t cap = 256;
    char *buf = (char*)malloc(cap);
    if (!buf) return NULL;

    size_t pos = 0;
    buf[pos++] = '[';

    QNode *node = q->front;
    int first = 1;
    while (node) {
        char *escaped = json_escape(node->data);
        if (!escaped) {
            free(buf);
            return NULL;
        }

        size_t item_len = strlen(escaped) + 3; /* "..." 加可能的逗号 */
        if (pos + item_len >= cap) {
            cap = cap * 2 + item_len;
            char *new_buf = (char*)realloc(buf, cap);
            if (!new_buf) {
                free(escaped);
                free(buf);
                return NULL;
            }
            buf = new_buf;
        }

        if (!first) {
            buf[pos++] = ',';
        }
        buf[pos++] = '"';
        memcpy(buf + pos, escaped, strlen(escaped));
        pos += strlen(escaped);
        buf[pos++] = '"';

        free(escaped);
        first = 0;
        node = node->next;
    }

    buf[pos++] = ']';
    buf[pos] = '\0';
    return buf;
}


int queue_from_json(Queue *q, const char *json_str) {
    if (!q || !json_str) return -1;

    /* 跳过前导空白 */
    while (isspace((unsigned char)*json_str)) json_str++;

    if (*json_str != '[') return -1;
    json_str++;

    /* 逐项解析 */
    while (*json_str) {
        /* 跳过后导空白 */
        while (isspace((unsigned char)*json_str)) json_str++;

        if (*json_str == ']') break;  /* 数组结束 */
        if (*json_str == ',') {
            json_str++;
            continue;
        }

        /* 期望一个带引号的字符串 */
        if (*json_str != '"') return -1;
        json_str++;  /* 跳过头引号 */

        /* 收集字符串内容（含转义） */
        size_t cap = 256;
        char *item = (char*)malloc(cap);
        if (!item) return -1;
        size_t pos = 0;

        while (*json_str && *json_str != '"') {
            if (*json_str == '\\' && *(json_str + 1)) {
                /* 转义字符：原样保留，后续统一 unescape */
                if (pos + 2 >= cap) {
                    cap *= 2;
                    char *new_item = (char*)realloc(item, cap);
                    if (!new_item) { free(item); return -1; }
                    item = new_item;
                }
                item[pos++] = *json_str++;  /* \ */
                item[pos++] = *json_str++;  /* 转义码 */
            } else {
                if (pos + 1 >= cap) {
                    cap *= 2;
                    char *new_item = (char*)realloc(item, cap);
                    if (!new_item) { free(item); return -1; }
                    item = new_item;
                }
                item[pos++] = *json_str++;
            }
        }

        if (*json_str != '"') { free(item); return -1; }
        json_str++;  /* 跳过尾引号 */

        item[pos] = '\0';

        /* 反转义 */
        json_unescape_inplace(item);

        /* 入队 */
        queue_enqueue(q, item);
        free(item);
    }

    return 0;
}


/* ============================================================
 * 文件持久化
 * ============================================================ */

static char* read_file(const char *path) {
    FILE *fp = fopen(path, "rb");
    if (!fp) return NULL;

    fseek(fp, 0, SEEK_END);
    long size = ftell(fp);
    fseek(fp, 0, SEEK_SET);

    char *buf = (char*)malloc(size + 1);
    if (!buf) {
        fclose(fp);
        return NULL;
    }

    size_t read_len = fread(buf, 1, size, fp);
    buf[read_len] = '\0';
    fclose(fp);
    return buf;
}


static int write_file(const char *path, const char *content) {
    FILE *fp = fopen(path, "wb");
    if (!fp) return -1;
    size_t len = strlen(content);
    size_t written = fwrite(content, 1, len, fp);
    fclose(fp);
    return (written == len) ? 0 : -1;
}


/**
 * 从文件加载队列。
 * 如果文件不存在，返回一个空队列（这是正常情况）。
 */
static Queue* queue_load(void) {
    Queue *q = queue_create();
    if (!q) return NULL;

    char *json_str = read_file(QUEUE_DATA_FILE);
    if (!json_str) {
        return q;  /* 文件不存在 = 空队列 */
    }

    if (queue_from_json(q, json_str) != 0) {
        /* JSON 格式损坏，从空队列开始 */
        queue_clear(q);
    }

    free(json_str);
    return q;
}


/**
 * 将队列保存到文件。
 */
static int queue_save(const Queue *q) {
    char *json_str = queue_to_json(q);
    if (!json_str) return -1;
    int ret = write_file(QUEUE_DATA_FILE, json_str);
    free(json_str);
    return ret;
}


/* ============================================================
 * 简易 JSON 值提取器
 *
 * 从 stdin 读取一行 JSON，提取 "command" 和 "data" 字段的值。
 * 这不是完整的 JSON 解析器，仅处理本项目需要的简单格式：
 *   {"command": "<cmd>", "data": "<value>"}
 *
 * command 是必须字段，data 是可选字段。
 * ============================================================ */

static int extract_json_field(const char *json, const char *key, char *out, size_t out_size) {
    if (!json || !key || !out) return -1;

    /* 构造搜索模式: "key" */
    char pattern[128];
    snprintf(pattern, sizeof(pattern), "\"%s\"", key);

    const char *pos = strstr(json, pattern);
    if (!pos) return -1;

    pos += strlen(pattern);

    /* 跳过 : 和空白 */
    while (*pos && (*pos == ':' || isspace((unsigned char)*pos))) pos++;

    if (*pos != '"') return -1;
    pos++;  /* 跳过头引号 */

    /* 复制值直到尾引号（处理转义） */
    size_t i = 0;
    while (*pos && *pos != '"' && i < out_size - 1) {
        if (*pos == '\\' && *(pos + 1)) {
            pos++;
            switch (*pos) {
                case '"':  out[i++] = '"';  break;
                case '\\': out[i++] = '\\'; break;
                case 'n':  out[i++] = '\n'; break;
                case 't':  out[i++] = '\t'; break;
                case 'r':  out[i++] = '\r'; break;
                default:   out[i++] = '\\'; out[i++] = *pos; break;
            }
        } else {
            out[i++] = *pos;
        }
        pos++;
    }
    out[i] = '\0';
    return 0;
}


/* ============================================================
 * 主入口：处理来自 stdin 的 JSON 命令
 * ============================================================ */

int queue_main(int argc, char *argv[]) {
    (void)argc;
    (void)argv;

    /* 读取 stdin 的一行 JSON 输入 */
    char input[65536];
    if (!fgets(input, sizeof(input), stdin)) {
        printf("{\"status\":\"error\",\"message\":\"无法读取 stdin\"}\n");
        return 1;
    }

    /* 提取命令 */
    char command[64] = {0};
    if (extract_json_field(input, "command", command, sizeof(command)) != 0) {
        printf("{\"status\":\"error\",\"message\":\"缺少 command 字段\"}\n");
        return 1;
    }

    /* 加载持久化队列 */
    Queue *q = queue_load();
    if (!q) {
        printf("{\"status\":\"error\",\"message\":\"无法创建/加载队列\"}\n");
        return 1;
    }

    /* 路由命令 */
    if (strcmp(command, "enqueue") == 0) {
        /* 提取 data 字段 */
        char data[65536] = {0};
        if (extract_json_field(input, "data", data, sizeof(data)) != 0) {
            queue_destroy(q);
            printf("{\"status\":\"error\",\"message\":\"enqueue 需要 data 字段\"}\n");
            return 1;
        }

        if (queue_enqueue(q, data) != 0) {
            queue_destroy(q);
            printf("{\"status\":\"error\",\"message\":\"入队失败（内存不足）\"}\n");
            return 1;
        }

        queue_save(q);
        printf("{\"status\":\"ok\",\"result\":{\"enqueued\":true,\"queue_size\":%d}}\n", q->size);

    } else if (strcmp(command, "dequeue") == 0) {
        char *data = queue_dequeue(q);
        if (data) {
            queue_save(q);
            /* 输出 JSON 时需要对 data 做转义 */
            char *escaped = json_escape(data);
            printf("{\"status\":\"ok\",\"result\":%s}\n",
                   escaped ? escaped : "null");
            free(escaped);
            free(data);
        } else {
            printf("{\"status\":\"ok\",\"result\":null}\n");
        }

    } else if (strcmp(command, "peek") == 0) {
        char *data = queue_peek(q);
        if (data) {
            char *escaped = json_escape(data);
            printf("{\"status\":\"ok\",\"result\":%s}\n",
                   escaped ? escaped : "null");
            free(escaped);
            free(data);
        } else {
            printf("{\"status\":\"ok\",\"result\":null}\n");
        }

    } else if (strcmp(command, "size") == 0) {
        printf("{\"status\":\"ok\",\"result\":%d}\n", q->size);

    } else if (strcmp(command, "is_empty") == 0) {
        printf("{\"status\":\"ok\",\"result\":%s}\n",
               q->size == 0 ? "true" : "false");

    } else if (strcmp(command, "clear") == 0) {
        queue_clear(q);
        queue_save(q);
        printf("{\"status\":\"ok\",\"result\":{\"cleared\":true}}\n");

    } else {
        printf("{\"status\":\"error\",\"message\":\"未知命令: %s。支持: enqueue, dequeue, peek, size, is_empty, clear\"}\n",
               command);
    }

    queue_destroy(q);
    return 0;
}
