package com.peach.service;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.peach.entity.User;
import com.baomidou.mybatisplus.extension.service.IService;

import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.authority.SimpleGrantedAuthority;

import java.util.Collections;

/**
 * <p>
 *  服务类
 * </p>
 *
 * @author peach
 * @since 2025-01-24
 */
public interface UserService extends IService<User>, UserDetailsService {

    // 优化泛型声明
    IPage<User> pageC(IPage<User> page);

    // 优化泛型声明
    IPage<User> pageCC(IPage<User> page, Wrapper<User> wrapper);

    @Override
    default UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        User user = this.lambdaQuery().eq(User::getAccount, username).one();

        if (user == null) {
            throw new UsernameNotFoundException("用户不存在: " + username);
        }

        if ("N".equals(user.getIsValid())) {
            throw new UsernameNotFoundException("用户已被禁用: " + username);
        }

        return new org.springframework.security.core.userdetails.User(
                user.getAccount(),
                user.getPassword(),
                Collections.singletonList(new SimpleGrantedAuthority("ROLE_" + getRoleName(user.getRoleId())))
        );
    }

    // 将 private 方法改为 default 方法
    default String getRoleName(Integer roleId) {
        if (roleId == null) {
            return "USER";
        }
        switch (roleId) {
            case 0: return "SUPER_ADMIN";
            case 1: return "ADMIN";
            case 2: return "USER";
            default: return "USER";
        }
    }
}