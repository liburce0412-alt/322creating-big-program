#ifndef BINARY_SEARCH_H
#define BINARY_SEARCH_H

/* 二分查找 —— 按时间排序 / 定位时间记录
 *
 * 输入一个按时间戳升序排列的记录数组（JSON），
 * 支持：
 *   - 按时间戳精确查找
 *   - 按时间戳范围查找
 *   - 按记录 ID 查找（数组须按 ID 排序）
 */

/* ---------- 处理 main.c 路由的入口 ---------- */
/* 返回 JSON 结果字符串（调用者需 free），出错返回 NULL */
char* binary_search_handle(const char *action, const char *data_json);

#endif /* BINARY_SEARCH_H */
