/**
 * KMP 字符串匹配模块 — 李恩琪 + 余欣泽
 * TODO: 实现 KMP 算法进行字符串模式匹配
 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "kmp.h"

/* TODO: 实现 KMP 前缀表构建 */
static int* compute_lps(const char *pattern) {
    int m = strlen(pattern);
    int *lps = (int *)malloc(m * sizeof(int));
    if (!lps) return NULL;
    int len = 0;
    lps[0] = 0;
    int i = 1;
    while (i < m) {
        if (pattern[i] == pattern[len]) {
            len++;
            lps[i] = len;
            i++;
        } else {
            if (len != 0)
                len = lps[len - 1];
            else {
                lps[i] = 0;
                i++;
            }
        }
    }
    return lps;
}

/* TODO: 实现 KMP 搜索 */
static int kmp_search(const char *text, const char *pattern, int *matches) {
    int n = strlen(text);
    int m = strlen(pattern);
    int *lps = compute_lps(pattern);
    if (!lps) return 0;

    int i = 0, j = 0;
    int count = 0;
    while (i < n) {
        if (pattern[j] == text[i]) { i++; j++; }
        if (j == m) {
            matches[count++] = i - j;
            j = lps[j - 1];
        } else if (i < n && pattern[j] != text[i]) {
            if (j != 0) j = lps[j - 1];
            else i++;
        }
    }
    free(lps);
    return count;
}

void kmp_handler(const char *action, const char *json_data, char *output) {
    if (strcmp(action, "search") == 0) {
        /* 从 json_data 中提取 text 和 pattern */
        char text[2048] = {0}, pattern[256] = {0};

        char *p = strstr(json_data, "\"text\"");
        if (p) {
            p = strchr(p, ':');
            if (p) {
                p = strchr(p, '"');
                if (p) {
                    p++;
                    int i = 0;
                    while (*p && *p != '"' && i < 2047) text[i++] = *p++;
                }
            }
        }

        p = strstr(json_data, "\"pattern\"");
        if (p) {
            p = strchr(p, ':');
            if (p) {
                p = strchr(p, '"');
                if (p) {
                    p++;
                    int i = 0;
                    while (*p && *p != '"' && i < 255) pattern[i++] = *p++;
                }
            }
        }

        int matches[256] = {0};
        int count = kmp_search(text, pattern, matches);

        /* 构造 JSON 输出 */
        char matches_json[4096] = "[";
        char buf[32];
        for (int i = 0; i < count; i++) {
            if (i > 0) strcat(matches_json, ",");
            sprintf(buf, "%d", matches[i]);
            strcat(matches_json, buf);
        }
        strcat(matches_json, "]");

        snprintf(output, 8192,
                 "{\"success\":true,\"matches\":%s,\"count\":%d}",
                 matches_json, count);
    } else {
        snprintf(output, 8192,
                 "{\"success\":false,\"error\":\"Unknown action: %s\"}", action);
    }
}
