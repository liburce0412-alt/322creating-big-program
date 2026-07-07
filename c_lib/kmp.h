#ifndef KMP_H
#define KMP_H

/* KMP 字符串匹配 —— 时间记录关键词搜索
 *
 * 👤 李恩琪+余欣泽 负责填充实现
 *
 * 接口：
 *   - search:     在记录数组中搜索关键词，返回匹配项
 *   - build_lps:  构建 KMP 部分匹配表
 *   - match:      单次匹配检测
 */

/* 处理 main.c 路由的入口 */
char* kmp_handle(const char *action, const char *data_json);

#endif /* KMP_H */
