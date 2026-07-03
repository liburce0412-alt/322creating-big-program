/* kmp.c —— KMP 关键词搜索
 * 👤 李恩琪+余欣泽 负责填充实现
 *
 * 桩代码（使项目可编译）
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "kmp.h"

char* kmp_handle(const char *action, const char *data_json) {
    (void) data_json;
    if (!action) return strdup("{\"error\":\"missing action\"}");

    /* TODO: 实现 KMP 搜索逻辑 */

    char buf[256];
    snprintf(buf, sizeof(buf),
        "{\"message\":\"kmp module stub: action '%s' not yet implemented\"}", action);
    return strdup(buf);
}
