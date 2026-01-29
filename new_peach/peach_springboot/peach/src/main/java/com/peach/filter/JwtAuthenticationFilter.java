package com.peach.filter; // 建议创建一个新的 filter 包

import com.peach.util.JwtUtil;
import com.peach.service.UserService; // 导入 UserService 来加载 UserDetails
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;

@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    @Autowired
    private JwtUtil jwtUtil;

    @Autowired
    private UserService userService; // 使用 UserService 来加载 UserDetails

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {

        final String authorizationHeader = request.getHeader("Authorization");

        String username = null;
        String jwt = null;

        if (authorizationHeader != null && authorizationHeader.startsWith("Bearer ")) {
            jwt = authorizationHeader.substring(7); // 提取 Token 字符串
            try {
                username = jwtUtil.extractUsername(jwt);
            } catch (Exception e) {
                // Token 解析失败（例如过期、签名无效等）
                System.err.println("JWT Token 解析失败或无效: " + e.getMessage());
                // 这里可以选择返回401或直接让过滤器链继续，Spring Security会处理
            }
        }

        // 如果提取到了用户名，并且当前没有认证信息
        if (username != null && SecurityContextHolder.getContext().getAuthentication() == null) {

            UserDetails userDetails = this.userService.loadUserByUsername(username);

            // 验证 Token 是否有效
            if (jwtUtil.validateToken(jwt, userDetails)) {
                // 创建认证对象
                UsernamePasswordAuthenticationToken usernamePasswordAuthenticationToken =
                        new UsernamePasswordAuthenticationToken(userDetails, null, userDetails.getAuthorities());
                usernamePasswordAuthenticationToken
                        .setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                // 将认证对象设置到安全上下文中
                SecurityContextHolder.getContext().setAuthentication(usernamePasswordAuthenticationToken);
            } else {
                System.err.println("JWT Token 验证失败，可能已过期或不匹配用户");
            }
        }

        filterChain.doFilter(request, response); // 继续执行过滤器链
    }
}