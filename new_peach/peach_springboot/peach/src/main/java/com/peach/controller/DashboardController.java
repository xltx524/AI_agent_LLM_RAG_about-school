// 文件路径: src/main/java/com/peach/controller/DashboardController.java
package com.peach.controller;

import com.peach.common.Result;
import com.peach.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

/**
 * [新增] 仪表盘数据控制器
 * 专门用于提供首页仪表盘所需的数据
 */
@RestController
@RequestMapping("/dashboard")
public class DashboardController {

    // [关键] 注入 UserService，这样我们就能访问用户表
    @Autowired
    private UserService userService;

    /**
     * [新增] 提供仪表盘统计数据的接口
     * 地址为 /dashboard/stats
     * @return Result 包含统计数据的Map
     */
    @GetMapping("/stats")
    public Result getDashboardStats() {
        // --- 1. [真实数据] 从数据库获取总用户数 ---
        // userService.count() 是 MyBatis-Plus 提供的便捷方法，可以直接查询表的总行数
        long totalUsers = userService.count();

        // --- 2. [模拟数据] 为其他指标生成随机数 ---
        // TODO: 将来有对应业务时，需要从真实的 Service 中获取数据
        int todayConsultations = 1280; // 固定模拟值
        int pendingApplications = 32;   // 固定模拟值
        int weeklyVisits = 8543;        // 固定模拟值

        // --- 3. 组装返回数据 ---
        // 使用 Map 将所有数据包装起来，方便前端按 key 获取
        Map<String, Object> data = new HashMap<>();
        data.put("totalUsers", totalUsers);                 // [真实数据]
        data.put("todayConsultations", todayConsultations); // [模拟数据]
        data.put("pendingApplications", pendingApplications); // [模拟数据]
        data.put("weeklyVisits", weeklyVisits);             // [模拟数据]

        // 使用您项目中的 Result.success() 统一格式返回
        return Result.success(data);
    }
}