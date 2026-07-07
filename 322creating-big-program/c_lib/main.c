/*
 * main.c — C 模块统一入口
 *
 * 用法：echo '<json>' | ./campus_lib <module_name>
 *
 * 路由：根据 argv[1]（模块名）将 stdin 的 JSON 分发给对应模块。
 *       每个模块独立编译为 .o 文件，通过此入口统一调用。
 *
 * 支持的模块：
 *   queue        — AI 请求队列管理（丁超轶实现）
 *   （以下模块由其他组员实现后接入）
 *   linked_list  — AI 对话历史双向链表
 *   stack        — 时间记录撤销/重做
 *   kmp          — 关键词搜索
 *   hash_table   — 快速检索
 *   binary_search — 按时间排序/定位
 */

#include <stdio.h>
#include <string.h>

/* ============================================================
 * 各模块的主入口声明（extern）
 * ============================================================ */

/* queue.c */
extern int queue_main(int argc, char *argv[]);

/*
 * 以下模块入口由对应组员完成后取消注释：
 *
 * extern int linked_list_main(int argc, char *argv[]);
 * extern int stack_main(int argc, char *argv[]);
 * extern int kmp_main(int argc, char *argv[]);
 * extern int hash_table_main(int argc, char *argv[]);
 * extern int binary_search_main(int argc, char *argv[]);
 */


/* ============================================================
 * 主入口
 * ============================================================ */

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("{\"status\":\"error\",\"message\":\"用法: %s <module_name>\"}\n",
               argv[0]);
        printf("{\"status\":\"error\",\"message\":\"可用模块: queue\"}\n");
        return 1;
    }

    const char *module = argv[1];

    /* ---- 路由到各模块 ---- */

    if (strcmp(module, "queue") == 0) {
        return queue_main(argc, argv);
    }
    /*
     * 以下路由由对应组员完成后取消注释：
     *
     * else if (strcmp(module, "linked_list") == 0) {
     *     return linked_list_main(argc, argv);
     * } else if (strcmp(module, "stack") == 0) {
     *     return stack_main(argc, argv);
     * } else if (strcmp(module, "kmp") == 0) {
     *     return kmp_main(argc, argv);
     * } else if (strcmp(module, "hash_table") == 0) {
     *     return hash_table_main(argc, argv);
     * } else if (strcmp(module, "binary_search") == 0) {
     *     return binary_search_main(argc, argv);
     * }
     */
    else {
        printf("{\"status\":\"error\",\"message\":\"未知模块: %s。可用: queue\"}\n", module);
        return 1;
    }
}
