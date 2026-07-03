#ifndef STACK_H
#define STACK_H

/* 栈 —— 时间记录撤销/重做
 *
 * 👤 李恩琪+余欣泽 负责填充实现
 *
 * 接口：
 *   - push:    将记录 JSON 压入撤销栈
 *   - pop:     弹出最近记录（撤销）
 *   - redo_pop: 从重做栈弹回（重做）
 *   - clear:   清空两个栈
 *   - size:    查看撤销栈大小
 */

/* 处理 main.c 路由的入口 */
char* stack_handle(const char *action, const char *data_json);

#endif /* STACK_H */
