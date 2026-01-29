package com.peach.service.impl;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.peach.entity.User;
import com.peach.mapper.UserMapper;
import com.peach.service.UserService;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;

/**
 * <p>
 *  服务实现类
 * </p>
 *
 * @author peach
 * @since 2025-01-24
 */
@Service
public class UserServiceImpl extends ServiceImpl<UserMapper, User> implements UserService {

    @Resource
    private UserMapper userMapper; // 假设 pageC 和 pageCC 是 UserMapper 中的自定义方法

    @Override
    public IPage<User> pageC(IPage<User> page) {
        // 确保 UserMapper 接口中定义了 IPage<User> pageC(IPage<User> page);
        return userMapper.pageC(page);
    }

    @Override
    public IPage<User> pageCC(IPage<User> page, Wrapper<User> wrapper) { // 修正 Wrapper 的泛型
        // 确保 UserMapper 接口中定义了 IPage<User> pageCC(IPage<User> page, @Param("ew") Wrapper<User> wrapper);
        return userMapper.pageCC(page, wrapper);
    }
}