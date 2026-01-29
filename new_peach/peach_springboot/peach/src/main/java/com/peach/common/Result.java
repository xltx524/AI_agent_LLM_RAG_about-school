package com.peach.common;

// 移除了多余的 import javax.xml.crypto.Data;
import lombok.Data; // 确保你已经添加了Lombok依赖，并且IDE安装了Lombok插件

@Data
public class Result {
    private int code;//编码 200/400
    private String msg;//成功、失败
    private long total;//记录总数
    private Object data;//数据

    // 无参的失败方法，使用默认消息
    public static Result fail(){
        return result(400,"操作失败",0L,null); // 统一使用“操作失败”作为默认消息
    }

    /**
     * 新增的失败方法，接收一个消息字符串
     * @param msg 失败的具体消息
     * @return 包含失败信息和状态码的Result对象
     */
    public static Result fail(String msg){
        return result(400, msg, 0L, null);
    }

    // 无参的成功方法，使用默认消息
    public static Result success(){
        return result(200,"操作成功",0L,null); // 统一使用“操作成功”作为默认消息
    }

    /**
     * 成功方法，接收数据
     * @param data 返回的数据
     * @return 包含成功信息和数据的Result对象
     */
    public static Result success(Object data){
        return result(200,"操作成功",0L,data);
    }

    /**
     * 成功方法，接收数据和总数（用于分页）
     * @param data 返回的数据
     * @param total 记录总数
     * @return 包含成功信息、数据和总数的Result对象
     */
    public static Result success(Object data,long total){
        return result(200,"操作成功",total,data);
    }

    /**
     * 可选：添加一个接收自定义消息的成功方法，以保持与fail方法的一致性
     * @param msg 成功的具体消息
     * @return 包含成功信息和状态码的Result对象
     */
    public static Result success(String msg) {
        return result(200, msg, 0L, null);
    }

    /**
     * 核心的私有方法，用于构建Result对象
     * @param code 状态码
     * @param msg 消息
     * @param total 记录总数
     * @param data 数据
     * @return 构建好的Result对象
     */
    private static Result result(int code, String msg, long total, Object data) {
        Result res = new Result();
        res.setData(data);
        res.setMsg(msg);
        res.setCode(code);
        res.setTotal(total);
        return res;
    }

}