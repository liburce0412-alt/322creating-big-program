#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "binary_search.h"

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
                case 'n': result[j++] = '\n'; break;
                case 't': result[j++] = '\t'; break;
                case '"': result[j++] = '"';  break;
                case '\\':result[j++] = '\\'; break;
                default:  result[j++] = pos[i]; break;
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

/* 解析 JSON 数组中的记录，提取每个对象的 timestamp 字段到一个数组中 */
static int extract_records_array(const char *json, long long **timestamps_out, char ***records_out) {
    if (!json) return 0;
    const char *arr = json;
    /* 如果有 "records" 键，提取其值 */
    const char *key_pos = strstr(json, "\"records\"");
    if (key_pos) {
        arr = strchr(key_pos + 9, '[');
    } else {
        arr = strchr(json, '[');
    }
    if (!arr) return 0;
    arr++; /* 跳过 [ */

    /* 第一遍：计数 */
    int count = 0;
    const char *p = arr;
    while (*p) {
        while (*p && *p != '{' && *p != ']') p++;
        if (*p == ']' || *p == '\0') break;
        count++;
        int depth = 0;
        while (*p) {
            if (*p == '{') depth++;
            else if (*p == '}') { depth--; if (depth == 0) { p++; break; } }
            else if (*p == '"') { p++; while (*p && *p != '"') { if (*p == '\\') p++; if (*p) p++; } }
            p++;
        }
    }

    if (count == 0) {
        *timestamps_out = NULL;
        *records_out = NULL;
        return 0;
    }

    /* 分配数组 */
    long long *timestamps = (long long*) malloc(sizeof(long long) * count);
    char **records = (char**) malloc(sizeof(char*) * count);
    if (!timestamps || !records) {
        free(timestamps); free(records);
        *timestamps_out = NULL;
        *records_out = NULL;
        return 0;
    }

    /* 第二遍：提取每个对象及其时间戳 */
    p = arr;
    int idx = 0;
    while (*p && idx < count) {
        while (*p && *p != '{' && *p != ']') p++;
        if (*p == ']' || *p == '\0') break;

        const char *obj_start = p;
        int depth = 0;
        while (*p) {
            if (*p == '{') depth++;
            else if (*p == '}') { depth--; if (depth == 0) { p++; break; } }
            else if (*p == '"') { p++; while (*p && *p != '"') { if (*p == '\\') p++; if (*p) p++; } }
            p++;
        }
        size_t obj_len = p - obj_start;
        records[idx] = (char*) malloc(obj_len + 1);
        if (records[idx]) {
            memcpy(records[idx], obj_start, obj_len);
            records[idx][obj_len] = '\0';
        }
        timestamps[idx] = json_extract_long(obj_start, "timestamp", 0);
        idx++;
    }

    *timestamps_out = timestamps;
    *records_out = records;
    return count;
}

/* ========== 二分查找核心算法 ========== */

/* 二分查找精确匹配的时间戳，返回索引，未找到返回 -1 */
static int binary_search_by_timestamp(long long *arr, int n, long long target) {
    if (!arr || n <= 0) return -1;
    int left = 0, right = n - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] == target) return mid;
        if (arr[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}

/* 查找 >= target 的第一个位置（lower_bound） */
static int lower_bound(long long *arr, int n, long long target) {
    if (!arr || n <= 0) return 0;
    int left = 0, right = n;
    while (left < right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] < target) left = mid + 1;
        else right = mid;
    }
    return left;
}

/* 查找 > target 的第一个位置（upper_bound） */
static int upper_bound(long long *arr, int n, long long target) {
    if (!arr || n <= 0) return 0;
    int left = 0, right = n;
    while (left < right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] <= target) left = mid + 1;
        else right = mid;
    }
    return left;
}

/* 二分查找按 ID（记录数组须按 id 排序） */
static int binary_search_by_id(char **records, int n, int target_id) {
    if (!records || n <= 0) return -1;
    int left = 0, right = n - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        int mid_id = json_extract_int(records[mid], "id", -1);
        if (mid_id == target_id) return mid;
        if (mid_id < target_id) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}

/* ========== main.c 路由入口 ========== */

char* binary_search_handle(const char *action, const char *data_json) {
    if (!action) {
        return strdup("{\"error\":\"missing action\"}");
    }

    /* ---- 按时间戳精确查找 ---- */
    if (strcmp(action, "search_by_time") == 0) {
        long long target = json_extract_long(data_json, "target", 0);
        long long *timestamps = NULL;
        char **records = NULL;
        int n = extract_records_array(data_json, &timestamps, &records);
        if (n <= 0) {
            free(timestamps); free(records);
            return strdup("{\"found\":false,\"error\":\"empty or invalid records array\"}");
        }
        int idx = binary_search_by_timestamp(timestamps, n, target);
        char *result;
        if (idx >= 0 && idx < n && records[idx]) {
            size_t len = strlen(records[idx]) + 128;
            result = (char*) malloc(len);
            snprintf(result, len,
                "{\"found\":true,\"index\":%d,\"record\":%s}", idx, records[idx]);
        } else {
            result = strdup("{\"found\":false,\"message\":\"timestamp not found\"}");
        }
        for (int i = 0; i < n; i++) free(records[i]);
        free(records);
        free(timestamps);
        return result;
    }

    /* ---- 按 ID 查找 ---- */
    if (strcmp(action, "search_by_id") == 0) {
        int target_id = json_extract_int(data_json, "target_id", -1);
        long long *timestamps = NULL;
        char **records = NULL;
        int n = extract_records_array(data_json, &timestamps, &records);
        if (n <= 0) {
            free(timestamps); free(records);
            return strdup("{\"found\":false,\"error\":\"empty or invalid records array\"}");
        }
        int idx = binary_search_by_id(records, n, target_id);
        char *result;
        if (idx >= 0 && idx < n && records[idx]) {
            size_t len = strlen(records[idx]) + 128;
            result = (char*) malloc(len);
            snprintf(result, len,
                "{\"found\":true,\"index\":%d,\"record\":%s}", idx, records[idx]);
        } else {
            result = strdup("{\"found\":false,\"message\":\"id not found\"}");
        }
        for (int i = 0; i < n; i++) free(records[i]);
        free(records);
        free(timestamps);
        return result;
    }

    /* ---- 按时间范围查找 ---- */
    if (strcmp(action, "range_search") == 0) {
        long long start = json_extract_long(data_json, "start", 0);
        long long end   = json_extract_long(data_json, "end", 0);
        long long *timestamps = NULL;
        char **records = NULL;
        int n = extract_records_array(data_json, &timestamps, &records);
        if (n <= 0) {
            free(timestamps); free(records);
            return strdup("{\"count\":0,\"records\":[]}");
        }

        int lo = lower_bound(timestamps, n, start);
        int hi = upper_bound(timestamps, n, end);
        int match_count = hi - lo;

        /* 构建结果 JSON 数组 */
        size_t cap = 4096;
        size_t len = 0;
        char *result = (char*) malloc(cap);
        if (!result) {
            for (int i = 0; i < n; i++) free(records[i]);
            free(records); free(timestamps);
            return NULL;
        }
        result[0] = '\0';

        /* 手动拼接 */
        char header[128];
        snprintf(header, sizeof(header), "{\"count\":%d,\"records\":[", match_count);
        size_t hlen = strlen(header);
        memcpy(result + len, header, hlen);
        len += hlen;
        result[len] = '\0';

        for (int i = lo; i < hi && i < n; i++) {
            if (i > lo) {
                if (len + 2 >= cap) { cap *= 2; result = (char*) realloc(result, cap); }
                result[len++] = ',';
                result[len] = '\0';
            }
            size_t rlen = records[i] ? strlen(records[i]) : 0;
            if (len + rlen + 2 >= cap) { cap = (len + rlen) * 2 + 64; result = (char*) realloc(result, cap); }
            if (records[i]) {
                memcpy(result + len, records[i], rlen);
                len += rlen;
            }
            result[len] = '\0';
        }
        if (len + 3 >= cap) { cap *= 2; result = (char*) realloc(result, cap); }
        result[len++] = ']';
        result[len++] = '}';
        result[len] = '\0';

        for (int i = 0; i < n; i++) free(records[i]);
        free(records);
        free(timestamps);
        return result;
    }

    /* ---- 检查数组是否有序 ---- */
    if (strcmp(action, "is_sorted") == 0) {
        long long *timestamps = NULL;
        char **records = NULL;
        int n = extract_records_array(data_json, &timestamps, &records);
        if (n <= 1) {
            for (int i = 0; i < n; i++) free(records ? records[i] : NULL);
            free(records); free(timestamps);
            return strdup("{\"sorted\":true,\"count\":0}");
        }
        int sorted = 1;
        for (int i = 1; i < n; i++) {
            if (timestamps[i] < timestamps[i-1]) { sorted = 0; break; }
        }
        for (int i = 0; i < n; i++) free(records[i]);
        free(records); free(timestamps);
        char buf[128];
        snprintf(buf, sizeof(buf),
            "{\"sorted\":%s,\"count\":%d}", sorted ? "true" : "false", n);
        return strdup(buf);
    }

    char buf[256];
    snprintf(buf, sizeof(buf),
        "{\"error\":\"unknown action: %s\"}", action);
    return strdup(buf);
}
