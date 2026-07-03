/* stack.c —— 时间记录撤销/重做
 * 👤 李恩琪+余欣泽 负责填充实现
 *
 * 桩代码（使项目可编译）
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "stack.h"

char* stack_handle(const char *action, const char *data_json) {
    (void) data_json;
    if (!action) return strdup("{\"error\":\"missing action\"}");

    /* TODO: 实现栈的逻辑 —— push/pop/redo_pop/clear/size */

    char buf[256];
    snprintf(buf, sizeof(buf),
        "{\"message\":\"stack module stub: action '%s' not yet implemented\"}", action);
    return strdup(buf);
}
