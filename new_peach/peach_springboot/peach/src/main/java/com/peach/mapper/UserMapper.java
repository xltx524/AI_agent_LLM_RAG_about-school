package com.peach.mapper;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.Constants; // 用于 @Param(Constants.WRAPPER)
import com.peach.entity.User;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/**
 * <p>
 *  Mapper 接口
 * </p>
 *
 * @author peach
 * @since 2025-01-24
 */
@Mapper
public interface UserMapper extends BaseMapper<User> {

    // 修正 pageC 方法的返回类型泛型
    IPage<User> pageC(IPage<User> page);

    // 修正 pageCC 方法的返回类型泛型和 Wrapper 参数的泛型
    // @Param(Constants.WRAPPER) 是 MyBatis-Plus 传递 Wrapper 的标准做法
    IPage<User> pageCC(IPage<User> page, @Param(Constants.WRAPPER) Wrapper<User> wrapper);
}