/* kmp.c —— KMP (Knuth-Morris-Pratt) 字符串匹配算法
 * 👤 陈+丁超轶 负责实现
 *
 * 用于 CampusAI 的时间记录关键词搜索功能。
 * 对每一条记录的 description 和 category 字段执行 KMP 模式匹配。
 *
 * 支持操作：
 *   search        - 对记录数组执行 KMP 搜索
 *   match_single  - 单个字符串匹配测试
 *   build_lps     - 返回 LPS 数组（调试用）
 *
 * 协议：stdin/stdout JSON，由 main.c 统一路由
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "kmp.h"

/* ========== KMP 核心算法 ========== */

/*
 * build_lps_array - 构建 LPS (Longest Proper Prefix which is also Suffix) 数组
 *
 * 这是 KMP 算法的核心预处理步骤。
 * lps[i] = pattern[0..i] 的最长相等前后缀长度。
 *
 * 时间复杂度：O(m)，m = pattern 长度
 */
static int* build_lps_array(const char *pattern, int m) {
    if (!pattern || m <= 0) return NULL;

    int *lps = (int*) malloc(m * sizeof(int));
    if (!lps) return NULL;

    lps[0] = 0;  /* 单字符模式，无真前后缀 */
    int len = 0; /* 当前最长相等前后缀长度 */
    int i = 1;

    while (i < m) {
        if (pattern[i] == pattern[len]) {
            len++;
            lps[i] = len;
            i++;
        } else {
            if (len != 0) {
                /* 回退到上一个可能的前缀位置 */
                len = lps[len - 1];
            } else {
                lps[i] = 0;
                i++;
            }
        }
    }

    return lps;
}

/*
 * kmp_search - 在 text 中搜索 pattern，返回所有匹配的起始位置
 *
 * @param text:     待搜索的文本
 * @param pattern:  搜索模式（关键词）
 * @param matches:  输出参数，匹配位置的数组（调用者需释放）
 * @return:         匹配数量
 *
 * 时间复杂度：O(n + m)，n = text 长度，m = pattern 长度
 */
static int kmp_search(const char *text, const char *pattern, int **matches) {
    if (!text || !pattern || !matches) return 0;

    int n = (int) strlen(text);
    int m = (int) strlen(pattern);

    if (m == 0 || n == 0 || m > n) return 0;

    /* 构建 LPS 数组 */
    int *lps = build_lps_array(pattern, m);
    if (!lps) return 0;

    /* 预分配匹配位置数组（最多 n 个位置） */
    int *found = (int*) malloc(n * sizeof(int));
    if (!found) {
        free(lps);
        return 0;
    }
    int count = 0;

    int i = 0; /* text 的索引 */
    int j = 0; /* pattern 的索引 */

    while (i < n) {
        if (pattern[j] == text[i]) {
            i++;
            j++;
        }

        if (j == m) {
            /* 找到完整匹配 */
            found[count++] = i - j;
            /* 继续搜索下一个匹配（允许重叠） */
            j = lps[j - 1];
        } else if (i < n && pattern[j] != text[i]) {
            if (j != 0) {
                j = lps[j - 1];
            } else {
                i++;
            }
        }
    }

    free(lps);

    *matches = found;
    return count;
}

/* ========== JSON 辅助函数 ========== */

/* 从 JSON 字符串中提取指定 key 的字符串值 */
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
                case 'r':  result[j++] = '\r'; break;
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

/* 从 JSON 中提取整数 */
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

/* JSON 字符串转义 */
static char* json_escape(const char *src) {
    if (!src) return NULL;
    size_t len = strlen(src);
    size_t cap = len * 2 + 4;
    char *dst = (char*) malloc(cap);
    if (!dst) return NULL;
    size_t j = 0;
    for (size_t i = 0; i < len; i++) {
        char c = src[i];
        switch (c) {
            case '"':  dst[j++] = '\\'; dst[j++] = '"';  break;
            case '\\': dst[j++] = '\\'; dst[j++] = '\\'; break;
            case '\n': dst[j++] = '\\'; dst[j++] = 'n';  break;
            case '\r': dst[j++] = '\\'; dst[j++] = 'r';  break;
            case '\t': dst[j++] = '\\'; dst[j++] = 't';  break;
            default:   dst[j++] = c; break;
        }
    }
    dst[j] = '\0';
    return dst;
}

/* 提取嵌套的 data 对象 */
static char* json_extract_data_object(const char *json) {
    if (!json) return NULL;
    const char *pos = strstr(json, "\"data\"");
    if (!pos) return strdup(json);
    pos = strchr(pos, '{');
    if (!pos) return NULL;
    const char *start = pos;
    int depth = 0;
    while (*pos) {
        if (*pos == '{') depth++;
        else if (*pos == '}') {
            depth--;
            if (depth == 0) {
                size_t len = pos - start + 1;
                char *result = (char*) malloc(len + 1);
                if (!result) return NULL;
                memcpy(result, start, len);
                result[len] = '\0';
                return result;
            }
        } else if (*pos == '"') {
            pos++;
            while (*pos && *pos != '"') {
                if (*pos == '\\') pos++;
                if (*pos) pos++;
            }
        }
        pos++;
    }
    return strdup(json);
}

/* 动态字符串追加 */
static char* str_append(char *dst, size_t *cap, size_t *len, const char *src) {
    if (!src) return dst;
    size_t slen = strlen(src);
    if (*len + slen + 1 > *cap) {
        *cap = (*len + slen) * 2 + 64;
        char *tmp = (char*) realloc(dst, *cap);
        if (!tmp) { free(dst); return NULL; }
        dst = tmp;
    }
    memcpy(dst + *len, src, slen);
    *len += slen;
    dst[*len] = '\0';
    return dst;
}

static char* str_append_char(char *dst, size_t *cap, size_t *len, char c) {
    if (*len + 2 > *cap) {
        *cap = (*cap) * 2 + 16;
        char *tmp = (char*) realloc(dst, *cap);
        if (!tmp) { free(dst); return NULL; }
        dst = tmp;
    }
    dst[*len] = c;
    (*len)++;
    dst[*len] = '\0';
    return dst;
}

/* ========== 不区分大小写的 KMP 搜索 ========== */

/*
 * case_insensitive_kmp - 不区分大小写的 KMP 搜索
 * 先将 text 和 pattern 都转为小写再匹配，
 * 但返回的匹配位置基于原始 text。
 */
static int case_insensitive_kmp_search(const char *text, const char *pattern, int **matches) {
    if (!text || !pattern || !matches) return 0;

    int n = (int) strlen(text);
    int m = (int) strlen(pattern);

    if (m == 0 || n == 0 || m > n) return 0;

    /* 转为小写 */
    char *text_lower = (char*) malloc(n + 1);
    char *pattern_lower = (char*) malloc(m + 1);
    if (!text_lower || !pattern_lower) {
        free(text_lower);
        free(pattern_lower);
        return 0;
    }

    for (int i = 0; i < n; i++) {
        text_lower[i] = (text[i] >= 'A' && text[i] <= 'Z') ? text[i] + 32 : text[i];
    }
    text_lower[n] = '\0';

    for (int i = 0; i < m; i++) {
        pattern_lower[i] = (pattern[i] >= 'A' && pattern[i] <= 'Z') ? pattern[i] + 32 : pattern[i];
    }
    pattern_lower[m] = '\0';

    int count = kmp_search(text_lower, pattern_lower, matches);

    free(text_lower);
    free(pattern_lower);
    return count;
}

/* ========== main.c 路由入口 ========== */

char* kmp_handle(const char *action, const char *data_json) {
    if (!action) {
        return strdup("{\"error\":\"missing action\"}");
    }

    /* ---- search: 在记录数组中搜索关键词 ---- */
    if (strcmp(action, "search") == 0) {
        char *data = json_extract_data_object(data_json);
        char *keyword = json_extract_string(data ? data : data_json, "keyword");

        if (!keyword || strlen(keyword) == 0) {
            free(data);
            free(keyword);
            return strdup("{\"error\":\"keyword is required\"}");
        }

        /* 解析 records 数组 */
        const char *records_json = data ? data : data_json;
        const char *arr_start = strstr(records_json, "\"records\"");
        if (!arr_start) {
            free(data);
            free(keyword);
            return strdup("{\"keyword\":\"\",\"count\":0,\"matches\":[],\"source\":\"kmp\",\"error\":\"no records field\"}");
        }

        /* 找到数组的 [ */
        const char *arr = strchr(arr_start, '[');
        if (!arr) {
            free(data);
            free(keyword);
            return strdup("{\"keyword\":\"\",\"count\":0,\"matches\":[],\"source\":\"kmp\",\"error\":\"records is not an array\"}");
        }
        arr++; /* 跳过 [ */

        /* 遍历数组中的每个记录对象 */
        size_t cap = 4096;
        size_t len = 0;
        char *result_json = (char*) malloc(cap);
        if (!result_json) {
            free(data); free(keyword);
            return strdup("{\"error\":\"memory allocation failed\"}");
        }
        result_json[0] = '\0';

        int match_count = 0;
        const char *p = arr;

        result_json = str_append(result_json, &cap, &len, "{\"keyword\":\"");
        char *escaped_kw = json_escape(keyword);
        result_json = str_append(result_json, &cap, &len, escaped_kw ? escaped_kw : keyword);
        free(escaped_kw);
        result_json = str_append(result_json, &cap, &len, "\",\"source\":\"kmp\",\"matches\":[");

        while (*p) {
            /* 跳到下一个 { */
            while (*p && *p != '{' && *p != ']') p++;
            if (*p == ']' || *p == '\0') break;

            /* 找到这个对象的结束 } */
            const char *obj_start = p;
            int depth = 0;
            while (*p) {
                if (*p == '{') depth++;
                else if (*p == '}') {
                    depth--;
                    if (depth == 0) { p++; break; }
                } else if (*p == '"') {
                    p++;
                    while (*p && *p != '"') {
                        if (*p == '\\') p++;
                        if (*p) p++;
                    }
                }
                p++;
            }

            /* 提取该记录的 description 和 category */
            char *desc = json_extract_string(obj_start, "description");
            char *cat  = json_extract_string(obj_start, "category");
            char *rid  = json_extract_string(obj_start, "id");
            char *dur  = json_extract_string(obj_start, "duration_min");
            char *ca   = json_extract_string(obj_start, "created_at");

            /* 对 description 执行 KMP 搜索 */
            int matched = 0;
            int *matches = NULL;
            int count = 0;

            if (desc && strlen(desc) > 0) {
                count = case_insensitive_kmp_search(desc, keyword, &matches);
                if (count > 0) matched = 1;
                free(matches);
            }

            /* 对 category 也搜索（如果 description 中没有找到） */
            if (!matched && cat && strlen(cat) > 0) {
                count = case_insensitive_kmp_search(cat, keyword, &matches);
                if (count > 0) matched = 1;
                free(matches);
            }

            if (matched) {
                /* 将该记录加入结果 */
                if (match_count > 0) {
                    result_json = str_append_char(result_json, &cap, &len, ',');
                }

                size_t obj_len = p - obj_start;
                char *obj_copy = (char*) malloc(obj_len + 1);
                if (obj_copy) {
                    memcpy(obj_copy, obj_start, obj_len);
                    obj_copy[obj_len] = '\0';
                    result_json = str_append(result_json, &cap, &len, obj_copy);
                    free(obj_copy);
                }
                match_count++;
            }

            free(desc);
            free(cat);
            free(rid);
            free(dur);
            free(ca);
        }

        /* 闭合 JSON */
        char count_buf[32];
        snprintf(count_buf, sizeof(count_buf), "],\"count\":%d}", match_count);
        result_json = str_append(result_json, &cap, &len, count_buf);

        free(data);
        free(keyword);
        return result_json;
    }

    /* ---- match_single: 单字符串 KMP 匹配测试 ---- */
    if (strcmp(action, "match_single") == 0) {
        char *data = json_extract_data_object(data_json);
        char *text = json_extract_string(data ? data : data_json, "text");
        char *pattern = json_extract_string(data ? data : data_json, "pattern");
        int case_sensitive = json_extract_int(data ? data : data_json, "case_sensitive", 0);

        if (!text || !pattern) {
            free(data); free(text); free(pattern);
            return strdup("{\"error\":\"text and pattern are required\"}");
        }

        int *matches = NULL;
        int count;
        if (case_sensitive) {
            count = kmp_search(text, pattern, &matches);
        } else {
            count = case_insensitive_kmp_search(text, pattern, &matches);
        }

        /* 构建结果 JSON */
        size_t cap = 256 + count * 16;
        char *result = (char*) malloc(cap);
        if (!result) {
            free(data); free(text); free(pattern); free(matches);
            return strdup("{\"error\":\"memory allocation failed\"}");
        }
        size_t res_len = 0;
        result[0] = '\0';

        res_len += snprintf(result + res_len, cap - res_len,
            "{\"found\":%s,\"count\":%d,\"positions\":[",
            count > 0 ? "true" : "false", count);

        for (int i = 0; i < count; i++) {
            if (i > 0) {
                res_len += snprintf(result + res_len, cap - res_len, ",");
            }
            res_len += snprintf(result + res_len, cap - res_len, "%d", matches[i]);
        }

        char *esc_text = json_escape(text);
        char *esc_pattern = json_escape(pattern);
        snprintf(result + res_len, cap - res_len,
            "],\"text\":\"%s\",\"pattern\":\"%s\"}",
            esc_text ? esc_text : "", esc_pattern ? esc_pattern : "");

        free(data); free(text); free(pattern); free(matches);
        free(esc_text); free(esc_pattern);
        return result;
    }

    /* ---- build_lps: 返回 LPS 数组（调试/学习用）---- */
    if (strcmp(action, "build_lps") == 0) {
        char *data = json_extract_data_object(data_json);
        char *pattern = json_extract_string(data ? data : data_json, "pattern");

        if (!pattern) {
            free(data);
            return strdup("{\"error\":\"pattern is required\"}");
        }

        int m = (int) strlen(pattern);
        int *lps = build_lps_array(pattern, m);

        size_t cap = 256 + m * 16;
        char *result = (char*) malloc(cap);
        if (!result) {
            free(data); free(pattern); free(lps);
            return strdup("{\"error\":\"memory allocation failed\"}");
        }
        size_t res_len = 0;
        result[0] = '\0';

        res_len += snprintf(result + res_len, cap - res_len,
            "{\"pattern\":\"%s\",\"length\":%d,\"lps\":[", pattern, m);

        if (lps) {
            for (int i = 0; i < m; i++) {
                if (i > 0) {
                    res_len += snprintf(result + res_len, cap - res_len, ",");
                }
                res_len += snprintf(result + res_len, cap - res_len, "%d", lps[i]);
            }
            free(lps);
        }

        snprintf(result + res_len, cap - res_len, "]}");

        free(data); free(pattern);
        return result;
    }

    /* 未知操作 */
    char buf[256];
    snprintf(buf, sizeof(buf),
        "{\"error\":\"unknown kmp action: %s\"}", action);
    return strdup(buf);
}
