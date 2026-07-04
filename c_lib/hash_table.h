/* ================================================================
 * hash_table.h —— 哈希表（快速检索用户/记录）
 *
 * 👤 李恩琪+余欣泽
 *
 * 采用链地址法（拉链法）解决哈希冲突，支持动态扩容。
 *
 * 接口：
 *   insert      - 插入 key-value 对
 *   search      - 按 key 查找
 *   delete      - 按 key 删除
 *   size        - 返回元素数量
 *   clear       - 清空
 *   keys        - 列出所有 key
 *   bulk_insert - 批量插入
 *
 * 协议：hash_table_handle(action, data_json) -> JSON 字符串（调用者 free）
 * ================================================================ */

#ifndef HASH_TABLE_H
#define HASH_TABLE_H

/* 处理 main.c 路由的入口 */
char* hash_table_handle(const char *action, const char *data_json);

#endif /* HASH_TABLE_H */
