package com.peach.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.StringUtils;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.peach.common.QueryPageParam;
import com.peach.common.Result;
import com.peach.entity.User;
import com.peach.service.UserService;
import com.peach.util.JwtUtil; // 导入 JwtUtil
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * <p>
 *  前端控制器
 * </p>
 *
 * @author peach
 * @since 2025-01-24
 */
@RestController
@RequestMapping("/user")
public class UserController {
    @Autowired
    private UserService userService;

    @Autowired // 注入 PasswordEncoder
    private PasswordEncoder passwordEncoder;

    @Autowired // 注入 AuthenticationManager
    private AuthenticationManager authenticationManager;

    @Autowired // 注入 JwtUtil
    private JwtUtil jwtUtil;

    @GetMapping("/list")
    public List<User> list(){
        return userService.list();
    }

    @GetMapping("/findByNo")
    public Result findByNo(@RequestParam String account){
        List<User> list = userService.lambdaQuery().eq(User::getAccount, account).list();
        if (!list.isEmpty()) {
            return Result.fail("账号已存在"); // 找到用户，表示账号已存在
        } else {
            return Result.success("账号可用"); // 未找到用户，表示账号可用
        }
    }

    // 【新增】根据用户名查询用户，用于注册时的唯一性校验
    @GetMapping("/findByName")
    public Result findByName(@RequestParam String name){
        List<User> list = userService.lambdaQuery().eq(User::getName, name).list();
        if (!list.isEmpty()) {
            return Result.fail("用户名已存在"); // 找到用户，表示用户名已存在
        } else {
            return Result.success("用户名可用"); // 未找到用户，表示用户名可用
        }
    }

    //增加
    @PostMapping("/save")
    public Result save(@RequestBody User user){
        if (user == null) {
            return Result.fail("用户信息为空");
        }
        // 新增用户时，密码不能为空
        if (StringUtils.isBlank(user.getPassword())) {
            return Result.fail("密码不能为空");
        }

        user.setIsValid("Y");
        // 对密码进行哈希加盐加密
        user.setPassword(passwordEncoder.encode(user.getPassword()));

        // 在保存前，可以再次进行账号和用户名的唯一性校验，防止并发或绕过前端校验
        if (!userService.lambdaQuery().eq(User::getAccount, user.getAccount()).list().isEmpty()) {
            return Result.fail("账号已存在");
        }
        if (!userService.lambdaQuery().eq(User::getName, user.getName()).list().isEmpty()) {
            return Result.fail("用户名已存在");
        }

        if (userService.save(user)) {
            return Result.success("用户添加成功");
        } else {
            return Result.fail("用户添加失败");
        }
    }

    // 登录 login
    @PostMapping("/login")
    public Result login(@RequestBody User user) {
        if (user == null || StringUtils.isBlank(user.getAccount()) || StringUtils.isBlank(user.getPassword())) {
            return Result.fail("账号或密码不能为空");
        }

        try {
            // 使用 AuthenticationManager 进行认证
            // 这会调用 UserDetailsService.loadUserByUsername 和 PasswordEncoder.matches
            Authentication authentication = authenticationManager.authenticate(
                    new UsernamePasswordAuthenticationToken(user.getAccount(), user.getPassword())
            );

            // 认证成功，获取用户详细信息
            UserDetails userDetails = (UserDetails) authentication.getPrincipal();
            User loggedInUser = userService.lambdaQuery().eq(User::getAccount, userDetails.getUsername()).one();

            // 检查用户是否被禁用 (如果UserDetailsService中没有处理)
            if (loggedInUser == null || "N".equals(loggedInUser.getIsValid())) {
                return Result.fail("用户已被禁用或不存在，请联系管理员");
            }

            // 生成 JWT Token
            String jwt = jwtUtil.generateToken(userDetails);

            String userRole = "user";
            if (loggedInUser.getRoleId() != null) {
                switch (loggedInUser.getRoleId()) {
                    case 0:
                        userRole = "super_admin";
                        break;
                    case 1:
                        userRole = "admin";
                        break;
                    case 2:
                        userRole = "user";
                        break;
                    default:
                        userRole = "user";
                        break;
                }
            }
            // 修改后的打印语句，现在包含了用户ID、账号、角色ID和映射角色
            System.out.println("用户 " + loggedInUser.getAccount() + " 登录成功，ID: " + loggedInUser.getId() + ", 角色ID: " + loggedInUser.getRoleId() + ", 映射角色: " + userRole);


            Map<String, Object> userMap = new HashMap<>();
            userMap.put("id", loggedInUser.getId()); // 这一行已经将用户的ID放入了userMap中
            userMap.put("account", loggedInUser.getAccount());
            userMap.put("name", loggedInUser.getName());
            userMap.put("phoneNum", loggedInUser.getPhoneNum());
            userMap.put("sex", loggedInUser.getSex());
            userMap.put("roleId", loggedInUser.getRoleId());
            userMap.put("role", userRole);

            HashMap<String, Object> responseData = new HashMap<>();
            responseData.put("user", userMap);
            responseData.put("token", jwt); // 将 JWT Token 返回给前端

            List<HashMap<String, String>> mockMenu = new ArrayList<>();
            if ("super_admin".equals(userRole) || "admin".equals(userRole)) {
                mockMenu.add(new HashMap<String, String>() {{ put("name", "仪表盘"); put("path", "/Index"); put("icon", "HomeFilled"); }});
                mockMenu.add(new HashMap<String, String>() {{ put("name", "用户管理"); put("path", "/Index/Main"); put("icon", "UserFilled"); }});
            } else if ("user".equals(userRole)) {
                mockMenu.add(new HashMap<String, String>() {{ put("name", "用户首页"); put("path", "/Index/UserDashboard"); put("icon", "HomeFilled"); }});
                mockMenu.add(new HashMap<String, String>() {{ put("name", "我的申请"); put("path", "/user/my-applications"); put("icon", "Tickets"); }});
            }
            responseData.put("menu", mockMenu);

            return Result.success(responseData);

        } catch (AuthenticationException e) {
            // 认证失败（账号不存在或密码错误）
            System.err.println("登录失败: " + e.getMessage());
            return Result.fail("账号或密码错误");
        }
    }

    //修改
    @PostMapping("/mod")
    public Result mod(@RequestBody User user){
        if (user == null || user.getId() == null) {
            return Result.fail("用户信息不完整");
        }

        // 如果提供了新密码，则对其进行哈希加盐加密
        if (StringUtils.isNotBlank(user.getPassword())) {
            user.setPassword(passwordEncoder.encode(user.getPassword()));
        } else {
            // 如果密码为空，则将其设置为null，MyBatis-Plus的updateById通常会忽略null字段，
            // 从而不更新数据库中现有的哈希密码。
            user.setPassword(null);
        }

        if (userService.updateById(user)) {
            return Result.success("用户信息修改成功");
        } else {
            return Result.fail("用户信息修改失败");
        }
    }

    //新增或修改
    @PostMapping("/saveOrMod")
    public Result saveOrMod(@RequestBody User user){
        if (user == null) {
            return Result.fail("用户信息为空");
        }

        if (user.getId() == null) { // 新增用户
            if (StringUtils.isBlank(user.getPassword())) {
                return Result.fail("新用户密码不能为空");
            }
            user.setPassword(passwordEncoder.encode(user.getPassword())); // 哈希新密码
            user.setIsValid("Y"); // 假设新用户默认有效
            // 同样进行账号和用户名的唯一性校验
            if (!userService.lambdaQuery().eq(User::getAccount, user.getAccount()).list().isEmpty()) {
                return Result.fail("账号已存在");
            }
            if (!userService.lambdaQuery().eq(User::getName, user.getName()).list().isEmpty()) {
                return Result.fail("用户名已存在");
            }
        } else { // 修改现有用户
            if (StringUtils.isNotBlank(user.getPassword())) {
                user.setPassword(passwordEncoder.encode(user.getPassword())); // 哈希新密码
            } else {
                // 如果密码为空，则设置为null，MyBatis-Plus会忽略，不更新现有密码
                user.setPassword(null);
            }
        }

        if (userService.saveOrUpdate(user)) {
            return Result.success("操作成功");
        } else {
            return Result.fail("操作失败");
        }
    }

    //删除
    @GetMapping("/delete")
    public Result delete(@RequestParam Integer id){
        if (userService.removeById(id)) {
            return Result.success("用户删除成功");
        } else {
            return Result.fail("用户删除失败");
        }
    }

    //查询（模糊匹配）
    @PostMapping("/listP")
    public Result listP(@RequestBody User user){
        LambdaQueryWrapper<User> lambdaQueryWrapper = new LambdaQueryWrapper<>();
        if (StringUtils.isNotBlank(user.getName())){
            lambdaQueryWrapper.like(User::getName, user.getName());
        }
        return Result.success(userService.list(lambdaQueryWrapper));
    }

    @PostMapping("/listPageC1")
    public Result listPageC1(@RequestBody QueryPageParam query){
        HashMap param = query.getParam();
        String searchText = (String)param.get("searchText");
        Integer roleId = (Integer)param.get("roleId");

        Page<User> page = new Page<>(query.getPageNum(), query.getPageSize());

        LambdaQueryWrapper<User> lambdaQueryWrapper = new LambdaQueryWrapper<>();

        if (StringUtils.isNotBlank(searchText)) {
            lambdaQueryWrapper.and(wrapper -> wrapper
                    .like(User::getName, searchText)
                    .or()
                    .like(User::getAccount, searchText)
                    .or()
                    .like(User::getPhoneNum, searchText)
            );
        }

        if (roleId != null) {
            lambdaQueryWrapper.eq(User::getRoleId, roleId);
        }

        IPage<User> result = userService.pageCC(page, lambdaQueryWrapper);
        return Result.success(result.getRecords(), result.getTotal());
    }

    /**
     * 新增后端功能：切换用户有效状态（禁用/启用）
     * 接收用户ID和目标状态 (Y/N)，更新用户的 isValid 字段
     */
    @PostMapping("/toggleStatus")
    public Result toggleUserStatus(@RequestBody User user) {
        if (user == null || user.getId() == null || StringUtils.isBlank(user.getIsValid())) {
            return Result.fail("请求参数不完整");
        }

        User existingUser = userService.getById(user.getId());
        if (existingUser == null) {
            return Result.fail("用户不存在");
        }

        existingUser.setIsValid(user.getIsValid());

        if (userService.updateById(existingUser)) {
            return Result.success("用户状态更新成功");
        } else {
            return Result.fail("用户状态更新失败");
        }
    }
}