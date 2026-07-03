#ifndef HASH_TABLE_H
#define HASH_TABLE_H

/* 哈希表 —— 快速检索记录/用户
 *
 * 👤 李恩琪+余欣泽 负责填充实现
 *
 * 接口：
 *   - insert:   插入 key-value 对
 *   - search:   按 key 查找
 *   - delete:   按 key 删除
 *   - size:     返回元素数量
 *   - clear:    清空
 */

/* 处理 main.c 路由的入口 */
char* hash_table_handle(const char *action, const char *data_json);

#endif /* HASH_TABLE_H */
